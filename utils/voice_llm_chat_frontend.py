class VoiceLLMChatFrontend_Colab:
    """Class generating Javascript frontend for VoiceLLMChatBackend in Colab.

    On the kernel side you need to register Google Colab callback functions:
    "notebook.new_chat"
    "notebook.fetch_data"
    "notebook.transcribe"
    "notebook.interrupt_response"
    "notebook.send_prompt"
    For example:
    google.colab.output.register_callback("notebook.send_prompt", send_user_prompt_function)
    """

    def __init__(self, assistantAvatarSrc = "", userAvatarSrc = ""):
        self.assistantAvatarSrc = assistantAvatarSrc
        self.userAvatarSrc = userAvatarSrc
        self.html_document_content = """<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Chat</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {
            margin: 0;
            padding: 20px;
        }

        @keyframes backgroundFade {
            0% {
                background-color: #ececec;
            }
            50% {
                background-color: #d0d0d0;
            }
            100% {
                background-color: #ececec;
            }
        }

        @keyframes dots {
            0% {
                content: ".";
            }
            33% {
                content: "..";
            }
            66% {
                content: "...";
            }
            100% {
                content: ".";
            }
        }

        .talking {
            animation: backgroundFade 1.3s ease-in-out infinite;
        }

        .talking::after {
            content: "...";
            display: inline-block;
            margin-left: 8px;
            color: black;
            animation: dots 1.5s steps(3, end) infinite;
        }

        #chatContainer {
            max-width: 800px;
            margin: 20px auto;
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
            height: 70vh;
            display: flex;
            flex-direction: column;
        }

        .message {
            display: flex;
            align-items: flex-start;
            margin: 10px 0;
        }

        .incoming {
            justify-content: flex-start;
        }

        .outgoing {
            justify-content: flex-end;
        }

        .message .avatar {
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            margin-top: auto;
            margin-bottom: auto;
        }

        .incoming .avatar {
            margin-right: 10px;
            margin-left: 0;
        }

        .outgoing .avatar {
            margin-left: 10px;
            margin-right: 0;
        }

        .message-content {
            display: flex;
            flex-direction: column;
            max-width: 70%;
        }

        .incoming .message-content {
            align-items: flex-start;
        }

        .outgoing .message-content {
            align-items: flex-end;
        }

        .message .text {
            padding: 10px;
            border-radius: 10px;
            max-width: 100%;
            word-wrap: break-word;
            position: relative;
        }

        .incoming .text {
            /* Light gray for incoming */
            background-color: #e0e0e0;
            color: black;
            /* Flat corner near the bubble point */
            border-bottom-left-radius: 0;

        }

        .outgoing .text {
            /* Blue for outgoing */
            background-color: #007bff;
            color: white;
            /* Flat corner near the bubble point */
            border-bottom-right-radius: 0;
        }

        /* Speech bubble points */
        .incoming .text::before {
            content: "";
            position: absolute;
            bottom: 0;
            /* Position to the left of the bubble */
            left: -7px;
            width: 0;
            height: 0;
            border-top: 8px solid transparent;
            border-bottom: 8px solid transparent;
            /* Color matches incoming bubble */
            border-right: 8px solid #e0e0e0;
        }

        .outgoing .text::before {
            content: "";
            position: absolute;
            bottom: 0;
            /* Position to the right of the bubble */
            right: -7px;
            width: 0;
            height: 0;
            border-top: 8px solid transparent;
            border-bottom: 8px solid transparent;
            /* Color matches outgoing bubble */
            border-left: 8px solid #007bff;
        }

        .timestamp {
            font-size: 10px;
            color: gray;
            margin-top: 5px;
            width: 100%;
        }

        .incoming .timestamp {
            text-align: left;
        }

        .outgoing .timestamp {
            text-align: right;
        }

        #inputArea {
            max-width: 800px;
            margin: 10px auto;
            display: flex;
            align-items: center;
            padding: 10px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }

        #textInput {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-right: 10px;
            font-size: 16px;
            font-family: sans-serif;
            resize: vertical;
            min-height: 40px;
            overflow-y: auto;
            line-height: 1.4;
        }

        #sendButton,
        #startRecordButton,
        #stopRecordButton,
        #newChatButton,
        #stopReplyButton {
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            color: white;
            font-size: 16px;
            transition: background-color 0.3s;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-right: 5px;
        }

        #sendButton {
            background-color: #28a745;
        }
        #sendButton:hover {
            background-color: #218838;
        }

        #startRecordButton {
            background-color: #dc3545;
        }
        #startRecordButton:hover {
            background-color: #c82333;
        }

        #stopRecordButton {
            background-color: #dc3545;
            display: none;
        }
        #stopRecordButton:hover {
            background-color: #c82333;
        }

        #newChatButton {
            background-color: #007bff;
        }
        #newChatButton:hover {
            background-color: #0056b3;
        }

        #stopReplyButton {
            background-color: #ffc107;
            color: black;
            display: none;
        }
        #stopReplyButton:hover {
            background-color: #e0a800;
        }

        #sendButton:disabled,
        #startRecordButton:disabled,
        #stopRecordButton:disabled,
        #newChatButton:disabled,
        #stopReplyButton:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }

        #recordingIndicator {
            margin-left: 10px;
            color: #dc3545;
            font-weight: bold;
            display: none;
        }

        #contextInfo {
            max-width: 800px;
            margin: 10px auto;
            padding: 10px;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            font-size: 14px;
            color: #555;
        }

        #contextInfo span {
            font-weight: bold;
            color: #000;
        }

    </style>
</head>

<body>
    <div id="chatContainer">
    </div>
    <div id="inputArea">
        <button id="newChatButton" title="Start New Chat"><i class="fas fa-plus"></i></button>
        <textarea id="textInput" placeholder="Type a message..."></textarea>
        <button id="sendButton" title="Send Message"><i class="fas fa-paper-plane"></i></button>
        <button id="startRecordButton" title="Start Recording"><i class="fas fa-microphone"></i></button>
        <button id="stopRecordButton" title="Stop Recording"><i class="fas fa-stop"></i></button>
        <button id="stopReplyButton" title="Stop Reply"><i class="fas fa-stop"></i></button>
        <span id="recordingIndicator">Recording...</span>
    </div>
    <div id="contextInfo">Current load of the context window (tokens): <span id="chatContextLen">0</span></div>

    <script>
        window.newChatButton = document.getElementById('newChatButton');
        window.startRecordButton = document.getElementById('startRecordButton');
        window.stopRecordButton = document.getElementById('stopRecordButton');
        window.stopReplyButton = document.getElementById('stopReplyButton');
        window.textInput = document.getElementById('textInput');
        window.sendButton = document.getElementById('sendButton');
        window.recordingIndicator = document.getElementById('recordingIndicator');
        window.chatContextLen = document.getElementById('chatContextLen');

        window.mediaRecorder;
        window.audioChunks = [];
        window.mediaStream;

        window.assistantAvatarSrc = "";
        window.userAvatarSrc = "";
        window.controller;
        window.messageCounter = 0;
        window.audioContext;
        window.audioQueue = [];
        window.isPlaying = false;
        window.audioSourceNode = null;
        window.isResponseFinished = false;

        function setButtonsEnabled(isEnabled) {
            window.newChatButton.disabled = !isEnabled;
            window.startRecordButton.disabled = !isEnabled;
            window.stopRecordButton.disabled = !isEnabled;
            window.stopReplyButton.disabled = !isEnabled;
            window.sendButton.disabled = !isEnabled;
        }

        function addMessage(content, assistant = false) {
            var chatContainer = document.getElementById("chatContainer");
            var messageDiv = document.createElement("DIV");
            var contentDiv = document.createElement("DIV");
            var textDiv = document.createElement("DIV");
            var timestampDiv = document.createElement("DIV");

            messageDiv.className = assistant ? "message incoming" : "message outgoing";

            var image = document.createElement("img");
            image.className = "avatar";
            if (assistant) {
                image.setAttribute("src", window.assistantAvatarSrc);
                image.setAttribute("alt", "Bielik");
                messageDiv.appendChild(image);
                window.messageCounter += 1;
                textDiv.setAttribute("id", "assistant_message_" + window.messageCounter.toString());
                image.setAttribute("id", "assistant_avatar_" + window.messageCounter.toString());
                textDiv.className = "text talking";
            } else {
                image.setAttribute("src", window.userAvatarSrc);
                image.setAttribute("alt", "User");
                textDiv.className = "text";
            }

            textDiv.innerText = content;
            timestampDiv.className = "timestamp";
            const currentDate = new Date();
            timestampDiv.innerText = currentDate.toLocaleString();

            contentDiv.className = "message-content";
            contentDiv.appendChild(textDiv);
            contentDiv.appendChild(timestampDiv);

            messageDiv.appendChild(contentDiv);

            if (!assistant) {
                messageDiv.appendChild(image);
            }

            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        };

        function updateMessage(content, replace = false) {
            let messageId = "assistant_message_" + window.messageCounter.toString();
            const textDiv = document.getElementById(messageId);
            if (textDiv) {
                if (replace) {
                    textDiv.innerText = content;
                } else {
                     if (textDiv.innerText !== '') {
                        textDiv.innerText += ' ' + content;
                    } else {
                        textDiv.innerText += content;
                    }
                }
            }
        }

        function respondingHasBeenFinished() {
            let messageId = "assistant_message_" + window.messageCounter.toString();
            const textDiv = document.getElementById(messageId);
            if (textDiv) {
                textDiv.classList.remove("talking");
            }
            window.sendButton.style.display = 'flex';
            window.stopReplyButton.style.display = 'none';
            setButtonsEnabled(true);
        }

        async function appendAudio(data) {
            if (!window.audioContext) {
                window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }

            const byteCharacters = atob(data.split(',')[1]);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);

            try {
                const audioBuffer = await window.audioContext.decodeAudioData(byteArray.buffer);
                window.audioQueue.push(audioBuffer);
                if (!window.isPlaying) {
                    playNextChunk();
                }
            } catch (e) {
                console.error("Error decoding audio data:", e);
            }
        }

        function playNextChunk() {
            if (window.controller && window.controller.signal.aborted) {
                stopAudioPlayback();
                return;
            }

            if (window.audioQueue.length > 0 && !window.isPlaying) {
                window.isPlaying = true;
                const audioBuffer = window.audioQueue.shift();
                window.audioSourceNode = window.audioContext.createBufferSource();
                window.audioSourceNode.buffer = audioBuffer;
                window.audioSourceNode.connect(window.audioContext.destination);
                window.audioSourceNode.onended = () => {
                    window.isPlaying = false;
                    window.audioSourceNode = null;
                    playNextChunk();
                };
                window.audioSourceNode.start();
            } else if (window.audioQueue.length === 0) {
                window.isPlaying = false;
                if (window.isResponseFinished)
                    respondingHasBeenFinished();
            }
        }

        function stopAudioPlayback() {
            if (window.audioSourceNode) {
                window.audioSourceNode.stop();
                window.audioSourceNode = null;
            }
            window.isPlaying = false;
            window.audioQueue = [];
            if (window.isResponseFinished)
                respondingHasBeenFinished();
        }

        async function streamResponse() {
            window.controller = new AbortController();
            const signal = controller.signal;
            window.isResponseFinished = false;
            window.sendButton.style.display = 'none';
            window.stopReplyButton.style.display = 'flex';
            try {
                while (true) {
                    if (signal.aborted) {
                        try {
                            let res = await google.colab.kernel.invokeFunction('notebook.interrupt_response', [], {});
                            const result = res.data['application/json'];
                            if (result.resp != '') {
                                updateMessage(result.resp, true);
                            }
                            if (result.context != '') {
                                 window.chatContextLen.innerText = result.context;
                            }
                            console.log("Generation stopped by user!");
                        } catch (e) {
                            console.error("Error calling interrupt_response:", e);
                        }
                        stopAudioPlayback();
                        setButtonsEnabled(true);
                        break;
                    }
                    let res;
                    try {
                        res = await google.colab.kernel.invokeFunction('notebook.fetch_data', [], {});
                        if (signal.aborted) continue;
                    } catch (e) {
                        console.error("Error during fetch_data call:", e);
                        break;
                    }
                    const result = res.data['application/json'];

                    if ('audio' in result) {
                        appendAudio(result.audio);
                    }
                    if (result.resp != '') {
                        updateMessage(result.resp);
                    }
                    if (result.finish == 'true') {
                        if (result.context != '') {
                            window.chatContextLen.innerText = result.context;
                        }
                        console.log("Response finished.");
                        break;
                    }
                    await new Promise(r => setTimeout(r, 50));
                }

            } catch (e) {
                if (e instanceof TypeError) {
                    console.log(e);
                } else {
                    console.error("Error in streamResponse:", e);
                }
            } finally {
                 window.controller = null;
                 window.isResponseFinished = true;
            }
        }

        window.startRecordButton.addEventListener('click', async () => {
            if (window.controller) {
                window.controller.abort();
                await new Promise(r => setTimeout(r, 200));
            }
            window.isResponseFinished = true;
            stopAudioPlayback();

            try {
                window.textInput.value = '';
                window.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                window.mediaRecorder = new window.MediaRecorder(window.mediaStream);
                window.audioChunks = [];

                window.mediaRecorder.ondataavailable = event => {
                    window.audioChunks.push(event.data);
                };

                window.mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(window.audioChunks, { type: 'audio/wav' });
                    const reader = new FileReader();
                    reader.onloadend = async () => {
                        const base64data = reader.result.split(',')[1];

                        try {
                            console.log("Recording finished.");
                            const result = await google.colab.kernel.invokeFunction('notebook.transcribe', [base64data], {});
                            console.log("Result from backend: ", result);
                            const transcribedText = result.data['application/json'].result;
                            textInput.value = transcribedText;
                            textInput.focus();

                        } catch (e) {
                            console.error('Error invoking Transcribe function:', e);
                            textInput.value = "Error transcribing audio.";
                        } finally {
                            setButtonsEnabled(true);
                            recordingIndicator.style.display = 'none';
                        }
                    };
                    reader.readAsDataURL(audioBlob);
                    window.mediaStream.getTracks().forEach(track => track.stop());
                };

                window.mediaRecorder.start();
                window.startRecordButton.style.display = 'none';
                window.stopRecordButton.style.display = 'flex';
                setButtonsEnabled(false);
                window.stopRecordButton.disabled = false;
                window.recordingIndicator.style.display = 'inline';

            } catch (err) {
                console.error('Error accessing microphone:', err);
                alert('Unable to access microphone. Please ensure you have granted permission.');
                window.startRecordButton.style.display = 'flex';
                window.stopRecordButton.style.display = 'none';
                setButtonsEnabled(true);
                window.recordingIndicator.style.display = 'none';
            }
        });

        window.stopRecordButton.addEventListener('click', () => {
            if (window.mediaRecorder && window.mediaRecorder.state !== 'inactive') {
                window.mediaRecorder.stop();
            }
            window.stopRecordButton.style.display = 'none';
            window.startRecordButton.style.display = 'flex';
        });

        window.textInput.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                if (!window.sendButton.disabled)
                    window.sendButton.click();
            }
        });

        window.sendButton.addEventListener('click', async () => {
            const messageText = window.textInput.value.trim();

            if (messageText) {
                setButtonsEnabled(false);

                if (window.controller) {
                    window.controller.abort();
                    await new Promise(r => setTimeout(r, 200));
                    stopAudioPlayback();
                }

                addMessage(messageText, false);
                addMessage("", true);
                window.textInput.value = '';

                const response = await google.colab.kernel.invokeFunction('notebook.send_prompt', [messageText], {});
                console.log(response);
                streamResponse();
                //setButtonsEnabled(true);
                window.stopReplyButton.disabled = false;
            }
        });

        window.stopReplyButton.addEventListener('click', () => {
            setButtonsEnabled(false);
            if (window.controller) {
                window.controller.abort();
            }
            window.isResponseFinished = true;
            stopAudioPlayback();
            window.sendButton.style.display = 'flex';
            window.stopReplyButton.style.display = 'none';
        });

        window.newChatButton.addEventListener('click', async () => {
            setButtonsEnabled(false);
            if (window.mediaRecorder && window.mediaRecorder.state !== 'inactive') {
                window.mediaRecorder.stop();
            }

            if (window.controller) {
                window.controller.abort();
                await new Promise(r => setTimeout(r, 200));
            }
            stopAudioPlayback();

            const response = await google.colab.kernel.invokeFunction('notebook.new_chat', [], {});

            messageCounter = 0;
            var chatContainer = document.getElementById("chatContainer");
            if (chatContainer)
                chatContainer.innerHTML = ""

            stopRecordButton.style.display = 'none';
            recordingIndicator.style.display = 'none';
            startRecordButton.style.display = 'flex';
            setButtonsEnabled(true);
            chatContextLen.innerText = "0";
        });

    </script>
</body>

</html>
"""

    def getDocument(self):
        return self.html_document_content.replace(
            'window.assistantAvatarSrc = "";', f'window.assistantAvatarSrc = "{self.assistantAvatarSrc}";'
        ).replace(
            'window.userAvatarSrc = "";', f'window.userAvatarSrc = "{self.userAvatarSrc}";'
        )
        