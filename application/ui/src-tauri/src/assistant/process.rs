// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

use std::path::Path;

use tokio::process::Command;

const CREATE_NO_WINDOW: u32 = 0x0800_0000;

fn is_batch(binary: &Path) -> bool {
    binary
        .extension()
        .and_then(|extension| extension.to_str())
        .is_some_and(|extension| {
            extension.eq_ignore_ascii_case("cmd") || extension.eq_ignore_ascii_case("bat")
        })
}

pub fn assistant_command(binary: &Path) -> Command {
    let mut command = if is_batch(binary) {
        let mut command = Command::new("cmd.exe");
        command.args(["/D", "/C"]);
        command.arg(binary);
        command
    } else {
        Command::new(binary)
    };
    command.creation_flags(CREATE_NO_WINDOW);
    command
}
