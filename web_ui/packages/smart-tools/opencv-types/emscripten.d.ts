// Code generated using https://github.com/peteruhnak/opencv-ts
// License: Apache-2.0
declare module 'emscripten' {
    function _malloc(size: number): number;
    function _free(ptr: number): void;

    const HEAP8: Int8Array;
    const HEAP16: Int16Array;
    const HEAP32: Int32Array;
    const HEAPU8: Uint8Array;
    const HEAPU16: Uint16Array;
    const HEAPU32: Uint32Array;
    const HEAPF32: Float32Array;
    const HEAPF64: Float64Array;

    class EmClassHandle {
        clone(): EmClassHandle;
        delete(): void;
        deleteLater(): unknown;
        isAliasOf(other: unknown): boolean;
        isDeleted(): boolean;
    }

    class EmVector<T> extends EmClassHandle {
        delete(): void;
        get(pos: number): T;
        push_back(value: T): void;
        resize(n: number, val: T): void;
        set(pos: number, value: T): boolean;
        size(): number;
    }
}
