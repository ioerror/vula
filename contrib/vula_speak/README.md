# Vula Speak
Vula speak introduces a new and alternative way to verify a vula peer using an out-of-band audio verification process. This folder contains all the work related to the new feature.

## Commands
- vula verify listen [-v, --verbose] *hostname*
- vula verify speak [-v, --verbose]

## Usage
You need a working audio input device such as a microphone and a working audio output device such as a speaker to use Vula Speak. You may only verify peers that you have already discovered through another mechanism such as mDNS or by scanning a QR code. The **vula organize** daemon must be running to use the **vula verify speak** or **vula verify listen** commands.

For a Vula peer to verify your Vula descriptor for the host **example.local** they must run **vula verify listen** to receive the audio data from your Vula enabled system:\
```vula verify [-v || -- verify] listen example.local```\
\
Send your Vula descriptor with **vula verify speak** run the following command:\
```vula verify [-v || -- verify] speak```

## Troubleshooting
Possible sources of verification trouble include:
- Ensure the audio output devices are functional. If you can't hear it, your Vula peer won't be able to hear it either.
- Ensure the audio input devices are functional. If your system can't record data with the system microphone, Vula won't be able to receive data.
- Low volume. Increase the volume output of the Vula client sending data.
- Background noise. Try to move to a quiet area without acoustical interference.
- Distance. Move closer the Vula systems closer together.

## Security Risk Analysis
As it is common new functions always bring new potential attack surfaces and thus new security risks. The **vula verify speak** and **vula verify listen** only runs when activated manually. We have taken care to select safe libraries for transmission, receiving, encoding, and decoding. Currently the process is not compartmentalized or run with reduced privileges. An adversary who is able to exploit the audio decoding library could theoretically exploit the Vula client running as your user.  
Even the best implementation can leave an application vulnerable to misuse, to reduce the possible security risks it is necessary to first be aware of those and analyse how they could be prevented respectively how the attack surface could be reduced as much as possible.\
Further security considerations and analysis is available in our **SecurityAnalysis.tex** document.

## Code
The **vula verify speak** and **vula verify listen** commands are integrated into the Vula project and only run when manually executed by a user.

## Dependencies
Both ggwave and pyaudio were added as soft dependencies with the vula speak and listen feature. The ggwave library is used to encode and decode messages into waveforms that are sent and received using pyaudio.
The ggwave library appears to be a popular and functional python library for audio communication.
[ggwave project](https://github.com/ggerganov/ggwave)\
\
ggwave >= v0.4.2 is recommended since previous versions caused memory leaks. ([BugReport](https://github.com/ggerganov/ggwave/issues/81#issuecomment-1397267232))\
\
The ggwave project is licensed under the MIT License and therefore compatible with the GNU General Public License (GNU GPL) that the vula project is licensed under.\
\
A python alternative for audio communication that was evaluated is [amodem](https://github.com/romanz/amodem). This would have been a pure python implementation introducing fewer dependencies, but it seems to be a less active project. Additionally, amodem was built to transmit files via sound and we weren't able to successfully integrate it into vula.

## Future work
The basic functionalities of the feature are implemented. Further contributions can be made specifically in regard to the following points:
*  Implement an acknowledge feature from listener to speaker
*  Write tests for the feature
