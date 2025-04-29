// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { MEDIA_CONTENT_BUCKET } from '../../../providers/media-upload-provider/media-upload.interface';
import { VALID_IMAGE_TYPES_SINGLE_UPLOAD, VALID_MEDIA_TYPES_DISPLAY } from '../../media-utils';
import { MediaDropBoxHeader } from './media-drop-box-header.component';

describe('MediaDropBoxHeader', () => {
    describe('Anomaly bucket', () => {
        it('should return only drag and drop image when it is a single image upload, without video', () => {
            render(
                <MediaDropBoxHeader
                    formats={VALID_IMAGE_TYPES_SINGLE_UPLOAD}
                    isMultipleUpload={false}
                    bucket={MEDIA_CONTENT_BUCKET.ANOMALOUS}
                />
            );
            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent('Drag and drop anomalous* image');
        });

        it('should return drag and drop image and video when it is a single image and video upload', () => {
            render(
                <MediaDropBoxHeader
                    formats={VALID_MEDIA_TYPES_DISPLAY}
                    isMultipleUpload={false}
                    bucket={MEDIA_CONTENT_BUCKET.ANOMALOUS}
                />
            );
            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent(
                'Drag and drop anomalous* image and video'
            );
        });

        it('should return drag and drop images and videos when it is multiple images and video upload', () => {
            render(<MediaDropBoxHeader formats={VALID_MEDIA_TYPES_DISPLAY} bucket={MEDIA_CONTENT_BUCKET.ANOMALOUS} />);
            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent(
                'Drag and drop anomalous* images and videos'
            );
        });
    });

    describe('Normal bucket', () => {
        it('should return only drag and drop image when it is a single image upload, without video', () => {
            render(
                <MediaDropBoxHeader
                    formats={VALID_IMAGE_TYPES_SINGLE_UPLOAD}
                    isMultipleUpload={false}
                    bucket={MEDIA_CONTENT_BUCKET.NORMAL}
                />
            );

            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent('Drag and drop normal image');
        });

        it('should return drag and drop image and video when it is a single image and video upload', () => {
            render(
                <MediaDropBoxHeader
                    formats={VALID_MEDIA_TYPES_DISPLAY}
                    isMultipleUpload={false}
                    bucket={MEDIA_CONTENT_BUCKET.NORMAL}
                />
            );

            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent(
                'Drag and drop normal image and video'
            );
        });

        it('should return drag and drop images and videos when it is multiple images and video upload', () => {
            render(<MediaDropBoxHeader formats={VALID_MEDIA_TYPES_DISPLAY} bucket={MEDIA_CONTENT_BUCKET.NORMAL} />);

            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent(
                'Drag and drop normal images and videos'
            );
        });
    });

    describe('Generic bucket', () => {
        it('should return only drag and drop image when it is a single image upload, without video', () => {
            render(
                <MediaDropBoxHeader
                    formats={VALID_IMAGE_TYPES_SINGLE_UPLOAD}
                    isMultipleUpload={false}
                    bucket={MEDIA_CONTENT_BUCKET.GENERIC}
                />
            );

            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent('Drag and drop image');
        });

        it('should return drag and drop image and video when it is a single image and video upload', () => {
            render(
                <MediaDropBoxHeader
                    formats={VALID_MEDIA_TYPES_DISPLAY}
                    isMultipleUpload={false}
                    bucket={MEDIA_CONTENT_BUCKET.GENERIC}
                />
            );

            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent('Drag and drop image and video');
        });

        it('should return drag and drop images and videos when it is multiple images and video upload', () => {
            render(<MediaDropBoxHeader formats={VALID_MEDIA_TYPES_DISPLAY} bucket={MEDIA_CONTENT_BUCKET.GENERIC} />);

            expect(screen.getByTestId('media-drop-box-header-id')).toHaveTextContent('Drag and drop images and videos');
        });
    });
});
