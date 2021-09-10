import os.path

import numpy as np
from scipy.io import wavfile
def encode(pathToAudio,stringToEncode):
    rate,audioData1 = wavfile.read(pathToAudio)
    stringToEncode = stringToEncode.ljust(100, '~')
    textLength = 8 * len(stringToEncode)

    blockLength = int(2 * 2 ** np.ceil(np.log2(2 * textLength)))
    blockNumber = int(np.ceil(audioData1.shape[0] / blockLength))
    audioData = audioData1.copy()
    # checks shape to change data to 1 axis
    if len(audioData1.shape) == 1:
        audioData.resize(blockNumber * blockLength, refcheck=False)
        audioData = audioData[np.newaxis]
    else:
        audioData.resize((blockNumber * blockLength, audioData.shape[1]), refcheck=False)
        audioData = audioData.T

    blocks = audioData[0].reshape((blockNumber, blockLength))

    # Calculate DFT using fft
    blocks = np.fft.fft(blocks)

    # calculate magnitudes
    magnitudes = np.abs(blocks)

    # create phase matrix
    phases = np.angle(blocks)

    # get phase differences
    phaseDiffs = np.diff(phases, axis=0)

    # conert message to encode into binary
    textInBinary = np.ravel([[int(y) for y in format(ord(x), "08b")] for x in stringToEncode])

    # Convert txt to phase differences
    textInPi = textInBinary.copy()
    textInPi[textInPi == 0] = -1
    textInPi = textInPi * -np.pi / 2

    blockMid = blockLength // 2

    # do phase conversion
    phases[0, blockMid - textLength: blockMid] = textInPi
    phases[0, blockMid + 1: blockMid + 1 + textLength] = -textInPi[::-1]

    # re compute  the ophase amtrix
    for i in range(1, len(phases)):
        phases[i] = phases[i - 1] + phaseDiffs[i - 1]

    # apply i-dft
    blocks = (magnitudes * np.exp(1j * phases))
    blocks = np.fft.ifft(blocks).real

    # combining all block of audio again
    audioData[0] = blocks.ravel().astype(np.int16)    

    wavfile.write("encoded.wav", rate, audioData.T)
    return "encoded.wav"


def decode(audioLocation):
    rate, audioData = wavfile.read(audioLocation)
    textLength = 800
    blockLength = 2 * int(2 ** np.ceil(np.log2(2 * textLength)))
    blockMid = blockLength // 2

    # get header info
    if len(audioData.shape) == 1:
        secret = audioData[:blockLength]
    else:
        secret = audioData[:blockLength, 0]

    # get the phase and convert it to binary
    secretPhases = np.angle(np.fft.fft(secret))[blockMid - textLength:blockMid]
    secretInBinary = (secretPhases < 0).astype(np.int8)

    #  convert into characters
    secretInIntCode = secretInBinary.reshape((-1, 8)).dot(1 << np.arange(8 - 1, -1, -1))

    # combine characters to original text
    return "".join(np.char.mod("%c", secretInIntCode)).replace("~", "")    
