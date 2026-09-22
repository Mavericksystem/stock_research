import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Top-level render-error safety net.
 *
 * Without this, any render-time exception anywhere in the tree unmounts
 * the whole app to a blank white screen — React's default behavior when
 * nothing catches the error. This only catches render/lifecycle errors;
 * async errors (fetch failures, stream errors) are handled separately at
 * their call sites (see app/App.tsx's try/catch around submit()).
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error("Unhandled render error:", error, info.componentStack);
  }

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#1f1d1a] px-6 text-center text-[#e5e0d8]">
          <p className="text-lg font-semibold">Something went wrong.</p>
          <p className="max-w-sm text-sm text-[#c5beb3]">
            Market Mind hit an unexpected error. Reloading usually fixes it.
          </p>
          <button
            type="button"
            onClick={this.handleReload}
            className="rounded-md bg-[#d97706] px-4 py-2 text-sm font-medium text-black"
          >
            Reload
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
