#!/usr/bin/env python3
"""
NENCY Virtual Assistant - All-in-One File
This file contains the complete NENCY virtual assistant application.
When run, it will create the necessary directory structure and files,
then start the Flask server.
"""

import os
import sys
import subprocess
import webbrowser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import platform
import time
from pathlib import Path

# Add this import at the top with other imports
from dotenv import load_dotenv

# Add this line before any environment variables are used
load_dotenv()

# Check if Flask is installed, if not provide instructions
try:
    from flask import Flask, render_template, request, jsonify, Response
except ImportError:
    print("Flask is not installed. Please install the required packages:")
    print("pip install flask requests google-generativeai")
    sys.exit(1)

# Try to import Google Generative AI, provide instructions if not available
try:
    import google.generativeai as genai
except ImportError:
    print("Google Generative AI package is not installed. Please install it:")
    print("pip install google-generativeai")
    print("\nContinuing without Gemini integration...")

# HTML Template as a string
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NENCY - Your Virtual Assistant</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-purple-900 to-indigo-800 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-10">
            <h1 class="text-5xl font-bold text-white mb-2">NENCY</h1>
            <p class="text-xl text-purple-200">Your Intelligent Virtual Assistant</p>
        </header>

        <div class="max-w-4xl mx-auto bg-white rounded-xl shadow-2xl overflow-hidden">
            <!-- Chat Container -->
            <div class="flex flex-col h-[600px]">
                <!-- Chat History -->
                <div id="chat-history" class="flex-1 p-6 overflow-y-auto">
                    <div class="assistant-message">
                        <div class="flex items-start mb-4">
                            <div class="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center text-white mr-3">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="bg-purple-100 rounded-lg p-3 max-w-[80%]">
                                <p>Hello! I'm NENCY, your virtual assistant. How can I help you today?</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Input Area -->
                <div class="border-t border-gray-200 p-4 bg-gray-50">
                    <div class="flex items-center">
                        <button id="voice-btn" class="w-12 h-12 rounded-full bg-purple-600 text-white flex items-center justify-center mr-3 hover:bg-purple-700 transition-colors">
                            <i class="fas fa-microphone"></i>
                        </button>
                        <input type="text" id="text-input" class="flex-1 border border-gray-300 rounded-full py-3 px-4 focus:outline-none focus:ring-2 focus:ring-purple-600" placeholder="Type your message or press the mic to speak...">
                        <button id="send-btn" class="w-12 h-12 rounded-full bg-purple-600 text-white flex items-center justify-center ml-3 hover:bg-purple-700 transition-colors">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Features Section -->
        <div class="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="bg-white bg-opacity-10 p-6 rounded-xl text-white">
                <div class="text-3xl mb-4"><i class="fas fa-search"></i></div>
                <h3 class="text-xl font-bold mb-2">Web Search</h3>
                <p>Ask NENCY to search Google or open websites for you.</p>
            </div>
            <div class="bg-white bg-opacity-10 p-6 rounded-xl text-white">
                <div class="text-3xl mb-4"><i class="fas fa-desktop"></i></div>
                <h3 class="text-xl font-bold mb-2">App Control</h3>
                <p>Launch applications with simple voice commands.</p>
            </div>
            <div class="bg-white bg-opacity-10 p-6 rounded-xl text-white">
                <div class="text-3xl mb-4"><i class="fas fa-brain"></i></div>
                <h3 class="text-xl font-bold mb-2">AI Powered</h3>
                <p>Get intelligent responses powered by Gemini 1.5 Pro.</p>
            </div>
        </div>

        <!-- Email Modal -->
        <div id="email-modal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center hidden z-50">
            <div class="bg-white rounded-xl p-6 max-w-md w-full">
                <h3 class="text-xl font-bold mb-4">Send Email</h3>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">To:</label>
                    <input type="email" id="email-recipient" class="w-full border border-gray-300 rounded p-2" readonly>
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Subject:</label>
                    <input type="text" id="email-subject" class="w-full border border-gray-300 rounded p-2">
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Message:</label>
                    <textarea id="email-message" class="w-full border border-gray-300 rounded p-2 h-32"></textarea>
                </div>
                <div class="flex justify-end">
                    <button id="cancel-email" class="bg-gray-300 text-gray-800 px-4 py-2 rounded mr-2">Cancel</button>
                    <button id="send-email" class="bg-purple-600 text-white px-4 py-2 rounded">Send</button>
                </div>
            </div>
        </div>

        <!-- Loading Indicator -->
        <div id="loading-indicator" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center hidden z-50">
            <div class="bg-white rounded-xl p-6 flex items-center">
                <div class="loader mr-3"></div>
                <p>NENCY is thinking...</p>
            </div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>
"""

# CSS as a string
CSS_CONTENT = """/* Custom animations and styles */
.loader {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-left-color: #9333ea;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.assistant-message, .user-message {
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.pulse {
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.listening {
    animation: listening 1.5s infinite;
    background-color: #ef4444 !important;
}

@keyframes listening {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

/* Scrollbar styling */
#chat-history::-webkit-scrollbar {
    width: 6px;
}

#chat-history::-webkit-scrollbar-track {
    background: #f1f1f1;
}

#chat-history::-webkit-scrollbar-thumb {
    background: #9333ea;
    border-radius: 3px;
}

#chat-history::-webkit-scrollbar-thumb:hover {
    background: #7e22ce;
}
"""

# JavaScript as a string
JS_CONTENT = """document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatHistory = document.getElementById('chat-history');
    const textInput = document.getElementById('text-input');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('voice-btn');
    const loadingIndicator = document.getElementById('loading-indicator');
    const emailModal = document.getElementById('email-modal');
    const emailRecipient = document.getElementById('email-recipient');
    const emailSubject = document.getElementById('email-subject');
    const emailMessage = document.getElementById('email-message');
    const sendEmailBtn = document.getElementById('send-email');
    const cancelEmailBtn = document.getElementById('cancel-email');

    // Speech recognition setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            voiceBtn.classList.add('listening');
            addSystemMessage("I'm listening...");
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            textInput.value = transcript;
            voiceBtn.classList.remove('listening');
            sendMessage();
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            voiceBtn.classList.remove('listening');
            addSystemMessage("Sorry, I couldn't hear you. Please try again.");
        };
        
        recognition.onend = function() {
            voiceBtn.classList.remove('listening');
        };
    } else {
        voiceBtn.style.display = 'none';
        alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
    }

    // Speech synthesis setup
    const synth = window.speechSynthesis;

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    textInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    voiceBtn.addEventListener('click', function() {
        if (recognition) {
            recognition.start();
        }
    });
    
    sendEmailBtn.addEventListener('click', sendEmailMessage);
    cancelEmailBtn.addEventListener('click', closeEmailModal);

    // Email handling variables
    let currentEmailRecipient = '';
    let emailStep = '';

    // Functions
    function sendMessage() {
        const message = textInput.value.trim();
        if (!message) return;
        
        // Handle email flow
        if (emailStep === 'subject') {
            emailSubject.value = message;
            addUserMessage(message);
            addSystemMessage("Great! Now, what's your message?");
            emailStep = 'message';
            textInput.value = '';
            return;
        } else if (emailStep === 'message') {
            emailMessage.value = message;
            addUserMessage(message);
            openEmailModal();
            emailStep = '';
            textInput.value = '';
            return;
        }
        
        addUserMessage(message);
        processCommand(message);
        textInput.value = '';
    }

    function processCommand(command) {
        showLoading();
        
        // Check if it's an email command
        if (command.toLowerCase().startsWith('send an email to')) {
            const recipient = command.toLowerCase().replace('send an email to', '').trim();
            currentEmailRecipient = recipient;
            emailRecipient.value = recipient;
            emailStep = 'subject';
            hideLoading();
            addAssistantMessage(`I'll help you send an email to ${recipient}. What's the subject?`);
            speakText(`I'll help you send an email to ${recipient}. What's the subject?`);
            return;
        }
        
        // Send to backend
        fetch('/process_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command: command }),
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            addAssistantMessage(data.response);
            speakText(data.response);
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            addSystemMessage("Sorry, I encountered an error processing your request.");
        });
    }

    function sendEmailMessage() {
        showLoading();
        closeEmailModal();
        
        fetch('/send_email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                recipient: emailRecipient.value,
                subject: emailSubject.value,
                message: emailMessage.value
            }),
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            addAssistantMessage(data.response);
            speakText(data.response);
            
            // Reset email form
            emailRecipient.value = '';
            emailSubject.value = '';
            emailMessage.value = '';
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            addSystemMessage("Sorry, I encountered an error sending your email.");
        });
    }

    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'user-message';
        messageDiv.innerHTML = `
            <div class="flex items-start justify-end mb-4">
                <div class="bg-purple-600 text-white rounded-lg p-3 max-w-[80%]">
                    <p>${escapeHtml(message)}</p>
                </div>
                <div class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center ml-3">
                    <i class="fas fa-user"></i>
                </div>
            </div>
        `;
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function addAssistantMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'assistant-message';
        messageDiv.innerHTML = `
            <div class="flex items-start mb-4">
                <div class="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center text-white mr-3">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="bg-purple-100 rounded-lg p-3 max-w-[80%]">
                    <p>${formatMessage(message)}</p>
                </div>
            </div>
        `;
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function addSystemMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'system-message';
        messageDiv.innerHTML = `
            <div class="flex justify-center mb-4">
                <div class="bg-gray-200 text-gray-700 rounded-lg p-2 max-w-[80%] text-sm">
                    <p>${escapeHtml(message)}</p>
                </div>
            </div>
        `;
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function formatMessage(message) {
        // Convert URLs to clickable links
        return escapeHtml(message).replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" class="text-purple-600 underline">$1</a>'
        );
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function speakText(text) {
        if (synth && !synth.speaking) {
            // Clean up text for speech (remove URLs, etc.)
            const cleanText = text.replace(/(https?:\/\/[^\s]+)/g, 'link');
            
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1;
            utterance.pitch = 1;
            synth.speak(utterance);
        }
    }

    function showLoading() {
        loadingIndicator.classList.remove('hidden');
    }

    function hideLoading() {
        loadingIndicator.classList.add('hidden');
    }

    function openEmailModal() {
        emailModal.classList.remove('hidden');
    }

    function closeEmailModal() {
        emailModal.classList.add('hidden');
    }

    // Add initial welcome message
    scrollToBottom();
});
"""

def setup_files():
    """Create the necessary directory structure and files"""
    # Create directories
    Path("templates").mkdir(exist_ok=True)
    Path("static/css").mkdir(parents=True, exist_ok=True)
    Path("static/js").mkdir(parents=True, exist_ok=True)
    
    # Write files
    with open("templates/index.html", "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE)
    
    with open("static/css/style.css", "w", encoding="utf-8") as f:
        f.write(CSS_CONTENT)
    
    with open("static/js/script.js", "w", encoding="utf-8") as f:
        f.write(JS_CONTENT)
    
    print("Files created successfully!")

# Create Flask application
app = Flask(__name__)

# Configure Gemini API if available
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your-gemini-api-key")
try:
    genai.configure(api_key=GEMINI_API_KEY)
    GEMINI_AVAILABLE = True
except:
    GEMINI_AVAILABLE = False
    print("Gemini API not configured. General questions will use a fallback response.")

# Weather API key
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "your-weather-api-key")

# Email configuration
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "your-email@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "your-app-password")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_command', methods=['POST'])
def process_command():
    data = request.json
    command = data.get('command', '').lower()
    
    # Process the command
    response = process_nency_command(command)
    
    return jsonify({"response": response})

def process_nency_command(command):
    # Google Search
    if "search for" in command:
        query = command.replace("search for", "").strip()
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        return f"Searching for {query} on Google."
    
    # Open website
    elif command.startswith("open ") and (".com" in command or ".org" in command or ".net" in command):
        website = command.replace("open ", "").strip()
        if not website.startswith("http"):
            website = "https://" + website
        webbrowser.open(website)
        return f"Opening {website}."
    
    # Open system application
    elif command.startswith("open ") or command.startswith("launch "):
        app_name = command.replace("open ", "").replace("launch ", "").strip()
        return open_application(app_name)
    
    # Weather information
    elif "weather" in command and "in" in command:
        try:
            city = command.split("in")[1].strip()
            return get_weather(city)
        except Exception as e:
            return f"Sorry, I couldn't get the weather information. Error: {str(e)}"
    
    # Send email
    elif command.startswith("send an email to"):
        recipient = command.replace("send an email to", "").strip()
        return f"I'll help you send an email to {recipient}. Please provide the subject."
    
    # For general questions, use Gemini if available
    else:
        try:
            if GEMINI_AVAILABLE:
                return ask_gemini(command)
            else:
                return "I'm not sure how to answer that. Gemini AI integration is not available."
        except Exception as e:
            return f"I encountered an error: {str(e)}"

def open_application(app_name):
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows application opening
            common_apps = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "paint": "mspaint.exe",
                "word": "winword.exe",
                "excel": "excel.exe",
                "chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "spotify": "spotify.exe"
            }
            
            app_executable = common_apps.get(app_name.lower(), app_name + ".exe")
            os.startfile(app_executable)
            
        elif system == "Darwin":  # macOS
            common_apps = {
                "safari": "Safari",
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "terminal": "Terminal",
                "notes": "Notes",
                "spotify": "Spotify"
            }
            
            app_to_open = common_apps.get(app_name.lower(), app_name)
            subprocess.Popen(["open", "-a", app_to_open])
            
        elif system == "Linux":
            common_apps = {
                "firefox": "firefox",
                "chrome": "google-chrome",
                "terminal": "gnome-terminal",
                "gedit": "gedit",
                "spotify": "spotify"
            }
            
            app_to_open = common_apps.get(app_name.lower(), app_name)
            subprocess.Popen([app_to_open])
            
        return f"Opening {app_name}."
    
    except Exception as e:
        return f"Sorry, I couldn't open {app_name}. Error: {str(e)}"

def get_weather(city):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
        response = requests.get(url)
        data = response.json()
        
        if "error" in data:
            return f"Sorry, I couldn't find weather information for {city}."
        
        location = data["location"]["name"]
        country = data["location"]["country"]
        temp_c = data["current"]["temp_c"]
        temp_f = data["current"]["temp_f"]
        condition = data["current"]["condition"]["text"]
        
        return f"Current weather in {location}, {country}: {condition} with a temperature of {temp_c}°C ({temp_f}°F)."
    
    except Exception as e:
        return f"Sorry, I couldn't get the weather information. Error: {str(e)}"

def send_email(recipient, subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, recipient, text)
        server.quit()
        
        return f"Email sent successfully to {recipient}!"
    
    except Exception as e:
        return f"Failed to send email. Error: {str(e)}"

def ask_gemini(question):
    if not GEMINI_AVAILABLE:
        return "I'm sorry, Gemini AI is not available right now."
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        return f"Sorry, I couldn't get a response from Gemini. Error: {str(e)}"

@app.route('/send_email', methods=['POST'])
def handle_email():
    data = request.json
    recipient = data.get('recipient', '')
    subject = data.get('subject', '')
    message = data.get('message', '')
    
    result = send_email(recipient, subject, message)
    return jsonify({"response": result})

def main():
    """Main function to run the application"""
    print("=" * 50)
    print("NENCY Virtual Assistant Setup")
    print("=" * 50)
    
    # Create files
    setup_files()
    
    # Check for API keys
    if GEMINI_API_KEY == "your-gemini-api-key":
        print("\nWARNING: Gemini API key not set. To enable AI responses, set the GEMINI_API_KEY environment variable.")
        print("You can get a key from: https://ai.google.dev/")
    
    if WEATHER_API_KEY == "your-weather-api-key":
        print("\nWARNING: Weather API key not set. To enable weather features, set the WEATHER_API_KEY environment variable.")
        print("You can get a free key from: https://www.weatherapi.com/")
    
    if EMAIL_ADDRESS == "your-email@gmail.com" or EMAIL_PASSWORD == "your-app-password":
        print("\nWARNING: Email credentials not set. To enable email features, set the EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.")
        print("For Gmail, you'll need to create an App Password: https://myaccount.google.com/apppasswords")
    
    print("\nStarting NENCY Virtual Assistant...")
    print("Open your browser and navigate to: http://127.0.0.1:5000/")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    # Run the Flask app
    app.run(debug=True)

if __name__ == "__main__":
    main()