import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false };

  public static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("CutoverProof interface error", error, info);
  }

  public render(): ReactNode {
    if (this.state.hasError) {
      return (
        <main className="fatal-state">
          <p className="eyebrow">Interface error</p>
          <h1>CutoverProof could not render this assessment.</h1>
          <p>Refresh the page. The underlying run evidence has not been changed.</p>
        </main>
      );
    }
    return this.props.children;
  }
}
