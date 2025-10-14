export default function Page() {
  return (
    <section>
      <h2>Welcome</h2>
      <p>Repository scaffold is in place. Backend services and Celery worker are stubbed. Live view and batch pipeline will be implemented next.</p>
      <ul>
        <li>Batch: Submit image → queue task → mocked processing</li>
        <li>Live: WebSocket stub at /ws/live/analysis</li>
      </ul>
    </section>
  );
}
