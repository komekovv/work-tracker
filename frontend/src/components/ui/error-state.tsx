import { Button } from "./button";
import { Card } from "./card";

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <Card className="p-6">
      <p className="text-sm font-medium text-foreground">
        Couldn&apos;t load data
      </p>
      <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      <p className="mt-1 text-xs text-muted-foreground">
        Is the backend API running?
      </p>
      {onRetry && (
        <Button variant="outline" className="mt-4" onClick={onRetry}>
          Retry
        </Button>
      )}
    </Card>
  );
}
