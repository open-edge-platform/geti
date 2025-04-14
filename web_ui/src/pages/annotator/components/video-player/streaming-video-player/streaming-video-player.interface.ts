// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// @see https://developer.mozilla.org/en-US/docs/Web/API/MediaError/code#media_error_code_constants
export enum VideoPlayerErrorReason {
    // The fetching of the associated resource was aborted by the user's request.
    MEDIA_ERR_ABORTED = 1,
    // Some kind of network error occurred which prevented the media from being successfully
    // fetched, despite having previously been available.
    MEDIA_ERR_NETWORK = 2,
    // Despite having previously been determined to be usable, an error occurred while trying
    // to decode the media resource, resulting in an error.
    MEDIA_ERR_DECODE = 3,
    MEDIA_ERR_SRC_NOT_SUPPORTED = 4,
}
