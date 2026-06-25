type ExceptionCapture = (exception: unknown) => unknown;

let captureException: ExceptionCapture | undefined;

export function configureExceptionCapture(capture: ExceptionCapture): void {
  captureException = capture;
}

export function captureServerException(exception: unknown): void {
  captureException?.(exception);
}

export function isExceptionCaptureConfigured(): boolean {
  return captureException !== undefined;
}
