import { useRef, useState } from "react";
import { askAssistant } from "../api";

interface Props {
  recipientId: string;
}

function getSpeechRecognition(): SpeechRecognitionLike | null {
  const Ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
  return Ctor ? new Ctor() : null;
}

export default function AskAssistant({ recipientId }: Props) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [asking, setAsking] = useState(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  const voiceSupported = typeof window !== "undefined" && !!(window.SpeechRecognition || window.webkitSpeechRecognition);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || asking) return;

    setAsking(true);
    setAnswer("");
    setLatencyMs(null);
    setError(null);

    await askAssistant(recipientId, question.trim(), {
      onChunk: (chunk) => setAnswer((prev) => prev + chunk),
      onDone: (latency) => {
        setLatencyMs(latency);
        setAsking(false);
      },
      onError: (message) => {
        setError(message);
        setAsking(false);
      },
    });
  }

  function toggleVoice() {
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    const recognition = getSpeechRecognition();
    if (!recognition) return;

    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuestion(transcript);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    setListening(true);
    recognition.start();
  }

  return (
    <section className="ask-assistant">
      <h2 className="today-section__heading">Ask about today</h2>
      <form onSubmit={handleAsk} className="ask-assistant__form">
        <input
          type="text"
          placeholder="e.g. Did Ravi give the morning tablet?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        {voiceSupported && (
          <button
            type="button"
            className={`ask-assistant__mic ${listening ? "ask-assistant__mic--active" : ""}`}
            onClick={toggleVoice}
            title="Ask with your voice"
            aria-label="Ask with your voice"
          >
            🎤
          </button>
        )}
        <button type="submit" disabled={asking || !question.trim()}>
          {asking ? "Thinking…" : "Ask"}
        </button>
      </form>

      {(answer || asking) && (
        <p className="ask-assistant__answer">
          {answer}
          {asking && <span className="ask-assistant__cursor">▍</span>}
        </p>
      )}
      {latencyMs !== null && <p className="ask-assistant__latency">Answered in {latencyMs} ms</p>}
      {error && <p className="add-task-form__error">{error}</p>}
    </section>
  );
}
