//! Desktop-only "Annotate with ChatGPT" assistant backend.
//!
//! Two independent ways to reach a model, both implemented here rather than in
//! the webview so that neither the API key nor the ChatGPT session token is
//! ever exposed to renderer JavaScript:
//!
//! * [`openai`] — bring-your-own OpenAI API key, stored in the OS credential
//!   store, streamed over the Responses API.
//! * [`codex`] — the user's existing ChatGPT subscription, driven through a
//!   private `codex app-server` subprocess.

pub mod codex;
pub mod openai;

pub use codex::CodexState;
pub use openai::OpenAiState;
