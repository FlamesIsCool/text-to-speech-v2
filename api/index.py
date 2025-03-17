import os
import io
import logging
from flask import Flask, request, send_file, jsonify, render_template_string
from gtts import gTTS
from serverless_wsgi import handle_request

# Enable debugging logs (these will show in your Vercel logs)
logging.basicConfig(level=logging.DEBUG)

# Embedded index.html content
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Text2Speech Converter</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          animation: {
            fadeIn: 'fadeIn 0.5s ease-out forwards'
          },
          keyframes: {
            fadeIn: {
              '0%': { opacity: 0 },
              '100%': { opacity: 1 }
            }
          }
        }
      }
    }
  </script>
</head>
<body class="bg-gray-900 text-white font-sans">
  <!-- Navigation -->
  <nav class="fixed w-full z-10 bg-gray-900 bg-opacity-90 shadow-lg">
    <div class="max-w-7xl mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center">
          <div class="text-2xl font-bold">Text2Speech</div>
        </div>
        <div class="hidden md:block">
          <div class="ml-10 flex items-baseline space-x-4">
            <a href="#hero" class="hover:text-gray-300 transition duration-200">Home</a>
            <a href="#features" class="hover:text-gray-300 transition duration-200">Features</a>
            <a href="#demo" class="hover:text-gray-300 transition duration-200">Demo</a>
            <a href="#faq" class="hover:text-gray-300 transition duration-200">FAQ</a>
            <a href="#testimonials" class="hover:text-gray-300 transition duration-200">Testimonials</a>
            <a href="#contact" class="hover:text-gray-300 transition duration-200">Contact</a>
          </div>
        </div>
        <!-- Mobile menu button -->
        <div class="md:hidden">
          <button id="menuBtn" class="focus:outline-none">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
    <!-- Mobile Menu -->
    <div id="mobileMenu" class="hidden md:hidden">
      <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
        <a href="#hero" class="block hover:text-gray-300 transition duration-200">Home</a>
        <a href="#features" class="block hover:text-gray-300 transition duration-200">Features</a>
        <a href="#demo" class="block hover:text-gray-300 transition duration-200">Demo</a>
        <a href="#faq" class="block hover:text-gray-300 transition duration-200">FAQ</a>
        <a href="#testimonials" class="block hover:text-gray-300 transition duration-200">Testimonials</a>
        <a href="#contact" class="block hover:text-gray-300 transition duration-200">Contact</a>
      </div>
    </div>
  </nav>

  <!-- Hero Section -->
  <section id="hero" class="pt-20 pb-32 bg-gradient-to-r from-gray-800 to-gray-900 text-center">
    <div class="max-w-3xl mx-auto">
      <h1 class="text-5xl md:text-6xl font-extrabold mb-6 animate-fadeIn">Bring Your Text to Life</h1>
      <p class="text-xl md:text-2xl text-gray-400 mb-8 animate-fadeIn delay-200">
        Experience cutting-edge text-to-speech conversion with our feature-rich, dark-themed converter.
      </p>
      <a href="#demo" class="inline-block bg-blue-600 hover:bg-blue-700 px-8 py-4 rounded-lg text-lg transition duration-200 animate-fadeIn delay-400">
        Try It Now
      </a>
    </div>
  </section>

  <!-- Features Section -->
  <section id="features" class="py-20 bg-gray-800">
    <div class="max-w-7xl mx-auto px-4">
      <h2 class="text-4xl font-bold text-center mb-12 animate-fadeIn">Features</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="bg-gray-900 p-6 rounded-lg shadow-lg hover:shadow-2xl transition duration-300 animate-fadeIn">
          <h3 class="text-2xl font-bold mb-4">High Quality TTS</h3>
          <p class="text-gray-400">Convert your text into natural and expressive speech with advanced synthesis.</p>
        </div>
        <div class="bg-gray-900 p-6 rounded-lg shadow-lg hover:shadow-2xl transition duration-300 animate-fadeIn delay-200">
          <h3 class="text-2xl font-bold mb-4">Downloadable Audio</h3>
          <p class="text-gray-400">Save your converted audio as MP3 files for offline listening anytime.</p>
        </div>
        <div class="bg-gray-900 p-6 rounded-lg shadow-lg hover:shadow-2xl transition duration-300 animate-fadeIn delay-400">
          <h3 class="text-2xl font-bold mb-4">Responsive Design</h3>
          <p class="text-gray-400">Enjoy a sleek, dark-themed interface optimized for desktops, tablets, and mobiles.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Demo Section -->
  <section id="demo" class="py-20">
    <div class="max-w-3xl mx-auto px-4">
      <h2 class="text-4xl font-bold text-center mb-8 animate-fadeIn">Try the Converter</h2>
      <div class="bg-gray-800 p-8 rounded-lg shadow-xl animate-fadeIn">
        <textarea id="textInput" rows="6" placeholder="Enter your text here..."
          class="w-full p-4 bg-gray-900 border border-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-white mb-6"></textarea>
        <div class="flex flex-col sm:flex-row justify-center items-center gap-4">
          <button id="playBtn" class="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded transition duration-200">
            Convert &amp; Play
          </button>
          <button id="saveBtn" class="w-full sm:w-auto bg-green-600 hover:bg-green-700 px-6 py-3 rounded transition duration-200">
            Save as MP3
          </button>
        </div>
        <!-- Loading Spinner -->
        <div id="loader" class="flex justify-center items-center mt-6 hidden">
          <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
        </div>
        <!-- Audio Element for Playback -->
        <div class="mt-6 text-center">
          <audio id="audioPlayer" controls class="w-full hidden"></audio>
        </div>
      </div>
    </div>
  </section>

  <!-- FAQ Section -->
  <section id="faq" class="py-20 bg-gray-800">
    <div class="max-w-5xl mx-auto px-4">
      <h2 class="text-4xl font-bold text-center mb-12 animate-fadeIn">Frequently Asked Questions</h2>
      <div class="space-y-4">
        <div class="bg-gray-900 p-4 rounded-lg shadow hover:shadow-lg transition duration-200">
          <button class="w-full text-left focus:outline-none faq-question">
            <span class="text-xl font-semibold">What is Text2Speech?</span>
          </button>
          <div class="faq-answer mt-2 text-gray-400 hidden">
            <p>Text2Speech converts your written text into natural-sounding speech using advanced text-to-speech technology.</p>
          </div>
        </div>
        <div class="bg-gray-900 p-4 rounded-lg shadow hover:shadow-lg transition duration-200">
          <button class="w-full text-left focus:outline-none faq-question">
            <span class="text-xl font-semibold">How does it work?</span>
          </button>
          <div class="faq-answer mt-2 text-gray-400 hidden">
            <p>Enter your text, click "Convert & Play" to listen or "Save as MP3" to download the audio. Our backend powered by gTTS handles the conversion.</p>
          </div>
        </div>
        <div class="bg-gray-900 p-4 rounded-lg shadow hover:shadow-lg transition duration-200">
          <button class="w-full text-left focus:outline-none faq-question">
            <span class="text-xl font-semibold">Is this service free?</span>
          </button>
          <div class="faq-answer mt-2 text-gray-400 hidden">
            <p>Yes, Text2Speech is completely free to use.</p>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Testimonials Section -->
  <section id="testimonials" class="py-20">
    <div class="max-w-7xl mx-auto px-4">
      <h2 class="text-4xl font-bold text-center mb-12 animate-fadeIn">What Our Users Say</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="bg-gray-800 p-6 rounded-lg shadow-lg animate-fadeIn">
          <p class="text-gray-400 italic mb-4">"This service transformed my workflow. High quality and super easy to use!"</p>
          <p class="font-bold">- Alex</p>
        </div>
        <div class="bg-gray-800 p-6 rounded-lg shadow-lg animate-fadeIn delay-200">
          <p class="text-gray-400 italic mb-4">"I love the dark theme—it’s modern and perfect for late night use."</p>
          <p class="font-bold">- Jamie</p>
        </div>
        <div class="bg-gray-800 p-6 rounded-lg shadow-lg animate-fadeIn delay-400">
          <p class="text-gray-400 italic mb-4">"An innovative solution for converting text to speech. The interface is sleek and intuitive."</p>
          <p class="font-bold">- Morgan</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Contact Section -->
  <section id="contact" class="py-20 bg-gray-800">
    <div class="max-w-3xl mx-auto px-4">
      <h2 class="text-4xl font-bold text-center mb-8 animate-fadeIn">Contact Us</h2>
      <form class="bg-gray-900 p-8 rounded-lg shadow-xl">
        <div class="mb-4">
          <label class="block text-gray-400 mb-2" for="name">Name</label>
          <input type="text" id="name" class="w-full p-3 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Your Name">
        </div>
        <div class="mb-4">
          <label class="block text-gray-400 mb-2" for="email">Email</label>
          <input type="email" id="email" class="w-full p-3 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="you@example.com">
        </div>
        <div class="mb-4">
          <label class="block text-gray-400 mb-2" for="message">Message</label>
          <textarea id="message" rows="4" class="w-full p-3 bg-gray-800 border border-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Your message"></textarea>
        </div>
        <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded transition duration-200">Send Message</button>
      </form>
    </div>
  </section>

  <!-- Footer -->
  <footer class="py-10 bg-gray-900 border-t border-gray-800">
    <div class="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center">
      <div class="mb-4 md:mb-0">
        <p>© 2025 Text2Speech. All rights reserved.</p>
      </div>
      <div class="flex space-x-4">
        <a href="#" class="hover:text-gray-300 transition duration-200">
          <svg fill="currentColor" class="w-6 h-6" viewBox="0 0 24 24">
            <path d="M22.46 6c-.77.35-1.6.59-2.46.69a4.31 4.31 0 001.88-2.38 8.59 8.59 0 01-2.73 1.04 4.28 4.28 0 00-7.3 3.9A12.14 12.14 0 013 4.88a4.28 4.28 0 001.32 5.72 4.24 4.24 0 01-1.94-.54v.05a4.28 4.28 0 003.43 4.2 4.3 4.3 0 01-1.93.07 4.28 4.28 0 004 2.97 8.58 8.58 0 01-5.31 1.83A8.7 8.7 0 012 19.54a12.1 12.1 0 006.55 1.92c7.86 0 12.17-6.52 12.17-12.17 0-.19 0-.39-.01-.58A8.7 8.7 0 0024 5.5a8.5 8.5 0 01-2.54.7z"></path>
          </svg>
        </a>
        <a href="#" class="hover:text-gray-300 transition duration-200">
          <svg fill="currentColor" class="w-6 h-6" viewBox="0 0 24 24">
            <path d="M12 2.2c3.4 0 3.8 0 5.2.1 1.4.1 2.2.3 2.7.6a5.4 5.4 0 012 1.1 5.4 5.4 0 011.1 2c.3.5.5 1.3.6 2.7.1 1.4.1 1.8.1 5.2s0 3.8-.1 5.2c-.1 1.4-.3 2.2-.6 2.7a5.4 5.4 0 01-1.1 2 5.4 5.4 0 01-2 1.1c-.5.3-1.3.5-2.7.6-1.4.1-1.8.1-5.2.1s-3.8 0-5.2-.1c-1.4-.1-2.2-.3-2.7-.6a5.4 5.4 0 01-2-1.1 5.4 5.4 0 01-1.1-2c-.3-.5-.5-1.3-.6-2.7C2.2 15.8 2.2 15.4 2.2 12s0-3.8.1-5.2c.1-1.4.3-2.2.6-2.7a5.4 5.4 0 011.1-2 5.4 5.4 0 012-1.1c.5-.3 1.3-.5 2.7-.6C8.2 2.2 8.6 2.2 12 2.2zm0 1.8C8.7 4 8.3 4 7 4.1 5.7 4.2 4.8 4.5 4 5a3.7 3.7 0 00-1.3 1.3A3.7 3.7 0 001 7c-.5.8-.8 1.7-.9 3-.1 1.3-.1 1.7-.1 5s0 3.7.1 5c.1 1.3.4 2.2.9 3a3.7 3.7 0 001.3 1.3 3.7 3.7 0 001.7.8c1.3.1 1.7.1 5 .1s3.7 0 5-.1c1.3-.1 2.2-.4 3-1a3.7 3.7 0 001.3-1.3 3.7 3.7 0 00.8-1.7c.1-1.3.1-1.7.1-5s0-3.7-.1-5c-.1-1.3-.4-2.2-.9-3a3.7 3.7 0 00-1.3-1.3 3.7 3.7 0 00-1.7-.8c-1.3-.1-1.7-.1-5-.1z"></path>
            <path d="M12 7.8a4.2 4.2 0 104.2 4.2A4.2 4.2 0 0012 7.8zm0 6.9a2.7 2.7 0 112.7-2.7 2.7 2.7 0 01-2.7 2.7z"></path>
            <circle cx="18.4" cy="5.6" r="1.1"></circle>
          </svg>
        </a>
      </div>
    </div>
  </footer>

  <!-- JavaScript -->
  <script>
    // Mobile menu toggle
    const menuBtn = document.getElementById('menuBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    menuBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
    });

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });

    // FAQ toggle functionality
    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(q => {
      q.addEventListener('click', () => {
        const answer = q.nextElementSibling;
        answer.classList.toggle('hidden');
      });
    });

    // Text-to-Speech Conversion and Save functionality
    const playBtn = document.getElementById('playBtn');
    const saveBtn = document.getElementById('saveBtn');
    const textInput = document.getElementById('textInput');
    const audioPlayer = document.getElementById('audioPlayer');
    const loader = document.getElementById('loader');

    // Convert & Play: Fetch the MP3 and play it
    playBtn.addEventListener('click', () => {
      const text = textInput.value.trim();
      if (!text) {
        alert("Please enter some text!");
        return;
      }
      loader.classList.remove('hidden');
      fetch('/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error("Conversion failed.");
        }
        return response.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        audioPlayer.src = url;
        audioPlayer.classList.remove('hidden');
        audioPlayer.play();
      })
      .catch(error => {
        alert("Error: " + error.message);
      })
      .finally(() => {
        loader.classList.add('hidden');
      });
    });

    // Save as MP3: Fetch the MP3 and trigger a download
    saveBtn.addEventListener('click', () => {
      const text = textInput.value.trim();
      if (!text) {
        alert("Please enter some text!");
        return;
      }
      loader.classList.remove('hidden');
      fetch('/save-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error("Failed to save audio.");
        }
        return response.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'output.mp3';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      })
      .catch(error => {
        alert("Error: " + error.message);
      })
      .finally(() => {
        loader.classList.add('hidden');
      });
    });
  </script>
</body>
</html>"""

app = Flask(__name__)

@app.route('/')
def index():
    try:
        return render_template_string(index_html)
    except Exception as e:
        logging.error("Error rendering index.html: %s", e)
        return "Error rendering index.html", 500

@app.route('/convert', methods=['POST'])
def convert_audio():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        tts = gTTS(text=text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return send_file(mp3_fp, mimetype="audio/mpeg")
    except Exception as e:
        logging.error("Error in convert_audio: %s", e)
        return jsonify({'error': str(e)}), 500

@app.route('/save-audio', methods=['POST'])
def save_audio():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        tts = gTTS(text=text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return send_file(mp3_fp, mimetype="audio/mpeg", as_attachment=True, download_name="output.mp3")
    except Exception as e:
        logging.error("Error in save_audio: %s", e)
        return jsonify({'error': str(e)}), 500

# Vercel's entry point using serverless-wsgi
def handler(event, context):
    return handle_request(app, event, context)

if __name__ == '__main__':
    # For local development run
    app.run(debug=True)
