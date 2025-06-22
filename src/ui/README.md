# AI Agent Chat UI

A ChatGPT-like frontend built with HTML, CSS, and TypeScript.

## Features

- 🎨 Modern, clean ChatGPT-inspired interface
- 💬 Real-time chat with typing indicators
- 📱 Responsive design for desktop and mobile
- 💾 Local chat history persistence
- 🔄 Session management with multiple conversations
- ⚡ Fast and lightweight

## File Structure

```
src/ui/
├── index.html      # Main HTML page
├── styles.css      # All styling and responsive design
├── chat.ts         # TypeScript source code
├── chat.js         # Compiled JavaScript (auto-generated)
└── README.md       # This file
```

## Quick Start

### Method 1: Using npm scripts
```bash
# Build the TypeScript (if you make changes)
npm run build-ui

# Serve the UI
npm run serve-ui
```

### Method 2: Using Python server
```bash
# From the project root
python3 src/serve_ui.py
```

### Method 3: Manual setup
```bash
# Compile TypeScript manually
npx tsc src/ui/chat.ts --target ES2020 --lib ES2020,DOM --outDir src/ui

# Serve with any HTTP server
cd src/ui
python3 -m http.server 8080
```

Then open http://localhost:8080 in your browser.

## API Integration

The frontend expects your AI Agent API to be running on `http://localhost:8000/api/chat` with the following format:

**Request:**
```json
{
  "message": "Hello, how are you?"
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you! How can I help you today?"
}
```

If the API is not available, the frontend will fall back to mock responses for demonstration purposes.

## Development

### Making Changes

1. Edit the TypeScript source (`chat.ts`)
2. Recompile: `npm run build-ui`
3. Refresh your browser

### Key Components

- **ChatApp class**: Main application controller
- **Message interface**: Type definition for chat messages
- **ChatSession interface**: Type definition for chat sessions
- **API integration**: Handles communication with the AI backend
- **Local storage**: Persists chat history between sessions

### Styling

The CSS uses a modern design system with:
- Inter font family for clean typography
- CSS Grid and Flexbox for layout
- CSS custom properties for theming
- Responsive breakpoints for mobile
- Smooth animations and transitions

### Browser Support

- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Customization

### Changing Colors
Edit the CSS custom properties in `styles.css`:
```css
:root {
  --primary-color: #10a37f;
  --sidebar-bg: #171717;
  --text-color: #333;
}
```

### Adding Features
- Extend the `Message` interface for new message types
- Add new methods to the `ChatApp` class
- Update the CSS for new UI elements

### API Configuration
Change the API endpoint in `chat.ts`:
```typescript
private apiBaseUrl = 'http://your-api-server:port/api';
```
