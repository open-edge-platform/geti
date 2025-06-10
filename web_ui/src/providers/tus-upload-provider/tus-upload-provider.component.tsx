// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useState } from 'react';

import { CSRF_HEADERS } from '@geti/core/src/services/security';
import { HttpStatusCode } from 'axios';
import { isEmpty } from 'lodash-es';
import { PreviousUpload, Upload, UploadOptions } from 'tus-js-client';

import { MissingProviderError } from '../../shared/missing-provider-error';

const FILE_CHUNK_SIZE = 1024 * 1024 * 10; // 10mb

interface UploadFileProps {
    file: File;
    endpoint: string;
    onError: UploadOptions['onError'];
    onProgress: UploadOptions['onProgress'];
    onSuccess: UploadOptions['onSuccess'];
}
interface TusUploadContextProps {
    abortActiveUpload: (id: string) => Promise<void>;
    setActiveUpload: (id: string, upload: Upload) => void;
    uploadFile: (props: UploadFileProps) => Upload;
}

const TusUploadContext = createContext<TusUploadContextProps | undefined>(undefined);

interface TusUploadProps {
    children: ReactNode;
}

export const TusUploadProvider = ({ children }: TusUploadProps): JSX.Element => {
    const [activeUploads, setActiveUploads] = useState<Map<string, Upload>>(new Map());

    const setActiveUpload = (id: string, upload: Upload): void => {
        activeUploads.set(id, upload);
        setActiveUploads(new Map(activeUploads));
    };

    const abortActiveUpload = async (id: string) => {
        const upload = activeUploads.get(id);

        upload && upload.abort();
        activeUploads.delete(id) && setActiveUploads(new Map(activeUploads));
    };

    const uploadFile = (props: UploadFileProps): Upload => {
        const { file, endpoint, onError, onProgress, onSuccess, ...rest } = props;

        const upload = new Upload(file, {
            endpoint,
            chunkSize: FILE_CHUNK_SIZE,
            retryDelays: [0, 1000, 3000, 5000],
            removeFingerprintOnSuccess: true,
            onBeforeRequest: (req) => {
                const xhr = req.getUnderlyingObject();
                xhr.withCredentials = true;
            },
            onShouldRetry: (error) => {
                // we should retry only when we have permission: we are authorized and has access to the resource
                // if it's not instance of Error it's instance of DetailedError
                if ('originalResponse' in error) {
                    const status = error.originalResponse?.getStatus() ?? 0;

                    if ([HttpStatusCode.Forbidden, HttpStatusCode.Unauthorized].includes(status)) {
                        return false;
                    }
                }

                return true;
            },
            headers: CSRF_HEADERS,
            onError,
            onProgress,
            onSuccess,
            ...rest,
        });

        upload.findPreviousUploads().then((previousUploads: PreviousUpload[]) => {
            if (!isEmpty(previousUploads)) {
                upload.resumeFromPreviousUpload(previousUploads[0]);
            }

            upload.start();
        });

        return upload;
    };

    return (
        <TusUploadContext.Provider
            value={{
                uploadFile,
                setActiveUpload,
                abortActiveUpload,
            }}
        >
            {children}
        </TusUploadContext.Provider>
    );
};

export const useTusUpload = (): TusUploadContextProps => {
    const context = useContext(TusUploadContext);

    if (context === undefined) {
        throw new MissingProviderError('useTusUpload', 'TusUploadProvider');
    }

    return context;
};
