// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MediaItem } from '../core/media/media.interface';
import { isVideoFrame } from '../core/media/video.interface';
import { downloadFile, getFileSize, loadImage } from './utils';

const getVideoSrcFromFrame = (frameSrc: string): string => {
    const videoSrcParts = frameSrc.split('frames');

    return videoSrcParts.length > 1 ? `${videoSrcParts[0]}display/stream` : frameSrc;
};

export const downloadMediaItem = (mediaItem: MediaItem) => {
    const itemSrc = isVideoFrame(mediaItem) ? getVideoSrcFromFrame(mediaItem.src) : mediaItem.src;

    // TODO(@jpggvilaca): Once extension exposure in media response is implemented
    // we can revert this "replace" and use the media item's mimetype to explicitly
    // set the file extension
    downloadFile(itemSrc, mediaItem.name.replaceAll('.', '_'));
};

export enum MEDIA_FILE_TYPE {
    IMAGE = 'Image',
    VIDEO = 'Video',
    UNKNOWN = 'Unknown',
}

const SPECIFIC_VIDEO_MIME_TYPES = ['quicktime', 'x-msvideo', 'x-matroska'];
const SPECIFIC_IMAGE_TYPES = ['tif', 'tiff'];

export const VALID_VIDEO_TYPES = ['mp4', 'avi', 'mkv', 'mov', 'webm', 'm4v'];
export const VALID_IMAGE_TYPES = ['jpg', 'jpeg', 'bmp', 'png', 'jfif', 'webp', ...SPECIFIC_IMAGE_TYPES];
export const VALID_IMAGE_TYPES_SINGLE_UPLOAD = ['jpg', 'jpeg', 'bmp', 'png'];
export const VALID_MEDIA_TYPES_DISPLAY = [...VALID_IMAGE_TYPES, ...VALID_VIDEO_TYPES];

export const VALIDATION_RULES = {
    MIN_WIDTH: 32, // Pixels
    MIN_HEIGHT: 32, // Pixels
    MAX_SIZE: 4.7 * 1024 * 1024 * 1024, // 4 GiB
    IMAGE: {
        MAX_WIDTH: 20000, // Pixels
        MAX_HEIGHT: 20000, // Pixels
    },
    VIDEO: {
        MAX_WIDTH: 7680, // Pixels 8K Resolution
        MAX_HEIGHT: 4320, // Pixels 8K Resolution
        MAX_LENGTH: 3 * 60 * 60, // 3 hours
    },
    INDEXED_DB: {
        MAX_SIZE: 1.01 * 1024 * 1024 * 1024, // 1 GiB
    },
};

export const loadImageFromFile = (imageFile: File) =>
    new Promise<HTMLImageElement>((resolve, reject) => {
        const fileReader = new FileReader();

        fileReader.onerror = reject;

        fileReader.onload = () => loadImage(String(fileReader.result)).then(resolve).catch(reject);

        fileReader.readAsDataURL(imageFile);
    });

export const loadVideoFromFile = (file: File) =>
    new Promise<HTMLVideoElement>((resolve, reject) => {
        const video = document.createElement('video');
        video.preload = 'metadata';

        video.onloadstart = () => resolve(video);

        video.onerror = (error) => {
            URL.revokeObjectURL(video.src);
            reject(error);
        };

        video.src = URL.createObjectURL(file);
    });

// MIME types only exist in the HTTP protocol, for the file system they are always deduced from the file extension
export const getFileExtensionFromName = (file: File): string | undefined => {
    const extRegex = /\.[0-9a-z]+$/i;

    return file.name.toLocaleLowerCase().match(extRegex)?.shift()?.slice(1);
};

export const isValidFileExtension = (file: File, validExtensions: string[]) => {
    const extension = getFileExtensionFromName(file);

    return extension && validExtensions.includes(extension);
};

const millisecondsToHours = (value: number) => value / 60 / 60;

export const defineMediaType = (file: File): MEDIA_FILE_TYPE | undefined => {
    const mediaType = file.type || getFileExtensionFromName(file);

    if (!mediaType) return MEDIA_FILE_TYPE.UNKNOWN;

    const isImage = VALID_IMAGE_TYPES.some((type: string): boolean =>
        mediaType.toLowerCase().endsWith(type.toLowerCase())
    );

    const isVideo = [...VALID_VIDEO_TYPES, ...SPECIFIC_VIDEO_MIME_TYPES].some((type: string): boolean =>
        mediaType.toLowerCase().endsWith(type.toLowerCase())
    );

    if (isImage) return MEDIA_FILE_TYPE.IMAGE;
    if (isVideo) return MEDIA_FILE_TYPE.VIDEO;

    return MEDIA_FILE_TYPE.UNKNOWN;
};

export const isVideoFile = (file: File): boolean => {
    return defineMediaType(file) == MEDIA_FILE_TYPE.VIDEO;
};

export const isTiffFormat = (file: File): boolean => {
    if (file.type) {
        const type = file.type.split('/').pop();

        return SPECIFIC_IMAGE_TYPES.includes(String(type));
    }

    return SPECIFIC_IMAGE_TYPES.includes(String(getFileExtensionFromName(file)));
};

export const VALIDATION_MESSAGES = {
    MISSING_MEDIA_TYPE: 'Your browser does not support folder upload, please upload one or more files.',
    // eslint-disable-next-line max-len
    UNSUPPORTED_MEDIA_TYPE: `Not a valid media format. Only the following are allowed: .${VALID_MEDIA_TYPES_DISPLAY.join(', .')}.`,
    IMAGE: {
        MIN_WIDTH: `Image width should be more than or equal ${VALIDATION_RULES.MIN_WIDTH} pixels`,
        MIN_HEIGHT: `Image height should be more than or equal ${VALIDATION_RULES.MIN_HEIGHT} pixels`,
        MAX_WIDTH: `Image width should be less than or equal ${VALIDATION_RULES.IMAGE.MAX_WIDTH} pixels`,
        MAX_HEIGHT: `Image height should be less than or equal ${VALIDATION_RULES.IMAGE.MAX_HEIGHT} pixels`,
        MAX_SIZE: `Image size should be less than or equal ${getFileSize(VALIDATION_RULES.MAX_SIZE, { base: 2 })}`,
        NOT_VALID_IMAGE: 'Not a valid image',
    },
    VIDEO: {
        MIN_WIDTH: `Video width should be more than or equal ${VALIDATION_RULES.MIN_WIDTH} pixels`,
        MIN_HEIGHT: `Video height should be more than or equal ${VALIDATION_RULES.MIN_HEIGHT} pixels`,
        MAX_WIDTH: `Video width should be less than or equal ${VALIDATION_RULES.VIDEO.MAX_WIDTH} pixels`,
        MAX_HEIGHT: `Video height should be less than or equal ${VALIDATION_RULES.VIDEO.MAX_HEIGHT} pixels`,
        MAX_SIZE: `Video size should be less than or equal ${getFileSize(VALIDATION_RULES.MAX_SIZE, { base: 2 })}`,
        MAX_LENGTH: `Video too long: the maximum duration is ${millisecondsToHours(
            VALIDATION_RULES.VIDEO.MAX_LENGTH
        )} hours`,
    },
};

export const getVideoDimensionErrors = ({ videoWidth, videoHeight }: HTMLVideoElement) => {
    const errors: string[] = [];

    if (videoWidth < VALIDATION_RULES.MIN_WIDTH) errors.push(VALIDATION_MESSAGES.VIDEO.MIN_WIDTH);
    if (videoWidth > VALIDATION_RULES.VIDEO.MAX_WIDTH) errors.push(VALIDATION_MESSAGES.VIDEO.MAX_WIDTH);
    if (videoHeight < VALIDATION_RULES.MIN_HEIGHT) errors.push(VALIDATION_MESSAGES.VIDEO.MIN_HEIGHT);
    if (videoHeight > VALIDATION_RULES.VIDEO.MAX_HEIGHT) errors.push(VALIDATION_MESSAGES.VIDEO.MAX_HEIGHT);

    return errors;
};
