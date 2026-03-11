interface Props {
  questions: string[];
  onClick: (question: string) => void;
}

export function SuggestedQuestions({ questions, onClick }: Props) {
  return (
    <div className="suggested-questions">
      <span className="suggestions-label">Suggested:</span>
      {questions.map((q, i) => (
        <button key={i} className="suggestion-chip" onClick={() => onClick(q)}>
          {q}
        </button>
      ))}
    </div>
  );
}
