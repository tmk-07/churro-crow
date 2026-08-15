export class ApiError extends Error {
  issues: string[];

  constructor(message: string, issues: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.issues = issues;
  }
}
