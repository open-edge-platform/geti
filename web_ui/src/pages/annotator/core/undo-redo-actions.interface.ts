// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface UndoRedoActions<State = unknown> {
    readonly canUndo: boolean;
    readonly canRedo: boolean;

    undo(): void;
    redo(): void;
    reset(state?: State): void;
}
