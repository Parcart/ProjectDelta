document.addEventListener('DOMContentLoaded', function () {
    const chatList = document.getElementById('chat-list');
    const chatWindow = document.getElementById('messages-container');
    const addChatButton = document.getElementById('add-chat-button');
    const attachButton = document.getElementById('attach-button');
    const fileInput = document.getElementById('file-input');
    const recordButton = document.getElementById('record-button');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const createChatModal = new bootstrap.Modal(document.getElementById('createChatModal'));
    const createChatForm = document.getElementById('create-chat-form');
    const chatNameInput = document.getElementById('chatName');
    let recorder;
    let audioChunks = [];

    function fetchChats() {
        chatList.innerHTML = ""; // Clear the list
        fetch('/chat/chats', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                data.chats.forEach(chat => {
                    const listItem = document.createElement('li');
                    listItem.classList.add('list-group-item', 'list-group-item-action');
                    listItem.textContent = chat.name; // Display chat name
                    listItem.dataset.chatId = chat.id; // Save chat id

                    listItem.addEventListener('click', () => {
                        chatList.querySelectorAll('li').forEach(li => li.classList.remove('active'));
                        listItem.classList.add('active');
                        chatWindow.innerHTML = "";
                        fetch(`/chat/messages/${chat.id}`, {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        })
                            .then(response => response.json())
                            .then(data => {
                                data.messages.forEach(message => {
                                    const messageDiv = document.createElement('div');
                                    messageDiv.classList.add('message', message.user_id == 1 ? 'bot-message' : 'user-message');
                                    if (message.type === "text") {
                                        messageDiv.textContent = message.content;
                                    } else if (message.type === "audio/mpeg") {
                                        const audio = document.createElement('audio');
                                        audio.controls = true;
                                        audio.src = `/static/uploads/${message.content}`; // Assuming content is the file path
                                        messageDiv.appendChild(audio);
                                    }
                                    else {
                                        const a = document.createElement('a');
                                        a.href = `/static/uploads/${message.content}`;
                                        a.textContent = message.name;
                                        messageDiv.appendChild(a);
                                    }
                                    chatWindow.appendChild(messageDiv);
                                    chatWindow.scrollTop = chatWindow.scrollHeight;
                                });
                            })
                            .catch(error => console.error('Error fetching messages: ', error));
                    });
                    chatList.appendChild(listItem);
                });
            })
            .catch(error => console.error('Error fetching chats: ', error));
    }

   addChatButton.addEventListener('click', function () {
       createChatModal.show();
   });


   createChatForm.addEventListener('submit', function (event) {
        event.preventDefault();
         const chatName = chatNameInput.value;
         createChatModal.hide();
          fetch('/chat/create', {
              method: 'POST',
              headers: {
                 'Content-Type': 'application/json'
              },
             body: JSON.stringify({ name: chatName }), // Send the chat name
           })
             .then(response => response.json())
            .then(data => {
                  chatNameInput.value = "";
                 fetchChats(); // Refresh chat
              })
             .catch(error => console.error('Error add chat: ', error))
    });

   attachButton.addEventListener('click', () => {
       fileInput.click();
   });

   fileInput.addEventListener('change', () => {
       const selectedFile = fileInput.files[0];
       if (selectedFile) {
           const reader = new FileReader();
           reader.onload = (event) => {
               sendMessage(event.target.result, selectedFile.type, selectedFile.name);
           };
           reader.readAsDataURL(selectedFile);
       }
   });

   recordButton.addEventListener('click', () => {
       if (recorder && recorder.state === "recording") {
           stopRecording();
       } else {
           startRecording();
       }
   });

   sendButton.addEventListener('click', () => {
       sendMessage(messageInput.value, "text", null);
       messageInput.value = "";
   });

    function startRecording() {
        navigator.mediaDevices.getUserMedia({audio: true})
            .then(stream => {
                recorder = new MediaRecorder(stream);
                audioChunks = [];
                recorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };
                recorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, {type: 'audio/mpeg'});
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        sendMessage(event.target.result, 'audio/mpeg', 'audio_recording.mp3');
                    };
                    reader.readAsDataURL(audioBlob);
                };
                recorder.start();
                recordButton.innerHTML = "<i class='fa fa-stop'></i>"; // Replace to stop
            })
            .catch(error => {
                console.error("Error start record: ", error);
                flashMessage("Error start record", 'danger');
            });
    }

    function stopRecording() {
        recorder.stop();
        recordButton.innerHTML = "<i class='fa fa-microphone'></i>";
    }


     function sendMessage(content, type, name) {
        const chatId = document.querySelector("#chat-list li.active")?.dataset.chatId;
        if (!chatId) {
            console.error("No active chat selected.");
            flashMessage("Please select a chat.", 'danger');
            return;
        }
        sendMessageHelper(content, type, name, chatId);
    }


    function sendMessageHelper(content, type, name, chatId) {
        const message = {content, type, name};
        fetch(`/chat/messages/${chatId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(message)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message', 'bot-message'); // Bot messages are always bot-message
                if (data.type === "text") {
                    messageDiv.textContent = data.content;
                }
                chatWindow.appendChild(messageDiv);
                chatWindow.scrollTop = chatWindow.scrollHeight;
            })
            .catch(error => {
                console.error('Error sending message:', error);
                flashMessage(`Error sending message: ${error.message}`, 'danger');
            });
    }


   function flashMessage(message, category) {
        const flashContainer = document.createElement('div');
        flashContainer.classList.add('container', 'mt-3');
        const alert = document.createElement('div');
        alert.classList.add('alert', `alert-${category}`, 'alert-dismissible', 'fade', 'show');
        alert.setAttribute('role', 'alert');
        alert.textContent = message;
        const button = document.createElement('button');
        button.setAttribute('type', 'button');
        button.classList.add('btn-close');
        button.setAttribute('data-bs-dismiss', 'alert');
        button.setAttribute('aria-label', 'Close');
       flashContainer.appendChild(alert);
       document.body.appendChild(flashContainer);

       setTimeout(() => {
           document.body.removeChild(flashContainer);
       }, 3000);
   }


    fetchChats();
});