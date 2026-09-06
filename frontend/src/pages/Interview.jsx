import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import * as api from "../lib/api";
import { useAuth } from "../context/AuthContext";

// Chrome/Edge only — everything degrades to plain typing everywhere else.
const SpeechRecognitionAPI =
  typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

export default function Interview() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [interviewId, setInterviewId] = useState(null);
  const [current, setCurrent] = useState(0);
  const [answer, setAnswer] = useState("");
  const [answers, setAnswers] = useState([]);
  const [started, setStarted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const baseAnswerRef = useRef(""); // text already in the box before the current listening session

  // Read each question aloud as soon as it appears.
  useEffect(() => {
    if (!started || !questions[current]) return;
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(questions[current]);
      utterance.rate = 0.95;
      window.speechSynthesis.speak(utterance);
    }
    setListening(false);
    recognitionRef.current?.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, started]);

  function replayQuestion() {
    if (typeof window !== "undefined" && window.speechSynthesis && questions[current]) {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(questions[current]));
    }
  }

  function toggleListening() {
    if (!SpeechRecognitionAPI) {
      setVoiceError("Voice input isn't supported in this browser — try Chrome, or just type your answer below.");
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      return;
    }

    setVoiceError("");
    baseAnswerRef.current = answer ? answer.trim() + " " : "";

    const recognition = new SpeechRecognitionAPI();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setAnswer(baseAnswerRef.current + transcript);
    };

    recognition.onerror = (event) => {
      setVoiceError(
        event.error === "not-allowed"
          ? "Microphone access was blocked — allow it in your browser's site settings to use voice input."
          : "Voice input stopped unexpectedly — you can keep typing instead."
      );
      setListening(false);
    };

    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  async function handleStart() {
    setError("");
    try {
      const data = await api.startInterview();
      setQuestions(data.questions);
      setInterviewId(data.interview_id);
      setStarted(true);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleNext() {
    recognitionRef.current?.stop();
    if (typeof window !== "undefined" && window.speechSynthesis) window.speechSynthesis.cancel();

    const nextAnswers = [...answers, { question: questions[current], answer: answer.trim() }];
    setAnswers(nextAnswers);
    setAnswer("");
    setVoiceError("");

    if (current + 1 < questions.length) {
      setCurrent((c) => c + 1);
      return;
    }

    setSubmitting(true);
    try {
      await api.submitInterview(interviewId, nextAnswers);
    } finally {
      navigate(`/interview/results/${interviewId}`);
    }
  }

  if (!started) {
    return (
      <Layout>
        <h1 className="font-display text-3xl mb-1">Interview</h1>
        <p className="text-muted text-sm mb-8">
          A personalized interview for <span className="text-paper">{user?.target_role || "your target role"}</span>.
          The AI reads each question aloud — answer by speaking or typing.
        </p>
        <button
          onClick={handleStart}
          className="bg-amber text-ink px-6 py-3 rounded-sm text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Start interview
        </button>
        {error && <p className="text-sm text-coral mt-4">{error}</p>}
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-xl mx-auto py-10">
        <p className="text-sm text-muted mb-8 font-mono text-center">AI interview</p>

        <div className="w-20 h-20 rounded-full bg-surface2 border border-line mx-auto mb-8 flex items-center justify-center text-3xl">
          🤖
        </div>

        <div className="flex items-start justify-center gap-3 mb-8 px-4">
          <p className="font-display text-2xl leading-snug text-center">"{questions[current]}"</p>
          <button
            onClick={replayQuestion}
            title="Hear the question again"
            className="shrink-0 mt-1 text-muted hover:text-amber transition-colors"
          >
            🔊
          </button>
        </div>

        <div className="relative mb-2">
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer, or press the mic and speak"
            rows={5}
            className="w-full bg-surface border border-line rounded-sm px-4 py-3 pr-14 text-sm text-paper focus:border-amber outline-none resize-none"
          />
          <button
            onClick={toggleListening}
            title={listening ? "Stop recording" : "Answer by voice"}
            className={`absolute bottom-3 right-3 w-9 h-9 rounded-full flex items-center justify-center border transition-colors ${
              listening
                ? "bg-coral/20 border-coral text-coral animate-pulse"
                : "bg-surface2 border-line text-muted hover:text-amber hover:border-amber"
            }`}
          >
            {listening ? "⏹️" : "🎙️"}
          </button>
        </div>

        {voiceError && <p className="text-xs text-coral mb-4 text-center">{voiceError}</p>}
        {listening && <p className="text-xs text-amber mb-4 text-center font-mono">Listening…</p>}

        <p className="text-sm text-muted mb-4 mt-4 font-mono text-center">
          Question {current + 1} / {questions.length}
        </p>

        <div className="text-center">
          <button
            onClick={handleNext}
            disabled={!answer.trim() || submitting}
            className="border border-line px-6 py-2.5 rounded-sm text-sm hover:border-amber hover:text-amber transition-colors disabled:opacity-50"
          >
            {submitting ? "Scoring…" : current + 1 < questions.length ? "Next question" : "Finish interview"}
          </button>
        </div>
      </div>
    </Layout>
  );
}
