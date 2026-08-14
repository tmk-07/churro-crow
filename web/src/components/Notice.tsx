export function Notice({ tone = "info", children }: {
  tone?: "info" | "warning" | "error" | "success";
  children: React.ReactNode;
}) {
  return <div className={`notice ${tone}`}>{children}</div>;
}

export function ErrorNotice({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : "Something went wrong.";
  const issues = error && typeof error === "object" && "issues" in error
    ? (error as { issues: string[] }).issues
    : [];
  return (
    <Notice tone="error">
      <strong>{message}</strong>
      {issues.length > 0 && <ul>{issues.map((issue) => <li key={issue}>{issue}</li>)}</ul>}
    </Notice>
  );
}
