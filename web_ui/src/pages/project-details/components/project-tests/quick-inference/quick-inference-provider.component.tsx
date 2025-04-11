// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, Dispatch, ReactNode, SetStateAction, useContext, useMemo, useState } from 'react';

import isEmpty from 'lodash/isEmpty';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Explanation } from '../../../../../core/annotations/prediction.interface';
import { PredictionResult } from '../../../../../core/annotations/services/prediction-service.interface';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import {
    isValidationFailReason,
    mediaExtensionHandler,
    validateMedia,
} from '../../../../../providers/media-upload-provider/media-upload.validator';
import { getImageData, getImageDataFromTiffFile } from '../../../../../shared/canvas-utils';
import {
    isTiffFormat,
    isValidFileExtension,
    loadImageFromFile,
    VALID_IMAGE_TYPES,
} from '../../../../../shared/media-utils';
import { MissingProviderError } from '../../../../../shared/missing-provider-error';
import { sortExplanationsByName } from '../../../../annotator/providers/prediction-provider/utils';
import { useQuickInferenceMutation } from './use-quick-inference-mutation.hook';

export interface QuickInferenceContextProps {
    isDisabled: boolean;
    isLoading: boolean;
    showWarningCard: boolean;
    image: ImageData | undefined;
    annotations: Annotation[];
    predictionResult?: PredictionResult;
    explanations: Explanation[];
    explanation?: Explanation;
    setExplanation: Dispatch<SetStateAction<Explanation | undefined>>;
    showExplanation: boolean;
    setShowExplanation: (value: boolean) => void;
    showPredictions: boolean;
    toggleShowPredictions: () => void;
    handleUploadImage: (files: File[] | FileList) => void;
    imageWasUploaded: boolean;
    dismissWarningCard: () => void;
    explanationOpacity: number;
    setExplanationOpacity: Dispatch<SetStateAction<number>>;
}

interface QuickInferenceProviderProps {
    isDisabled: boolean;
    children: ReactNode;
}

const QuickInferenceContext = createContext<QuickInferenceContextProps | undefined>(undefined);

export const QuickInferenceProvider = ({ isDisabled, children }: QuickInferenceProviderProps): JSX.Element => {
    const projectIdentifier = useProjectIdentifier();
    const { predictionMutation, explainMutation } = useQuickInferenceMutation();
    const { addNotification } = useNotification();

    const [warningCardDismissed, setDismissWarningCard] = useState(false);
    const [imageData, setImageData] = useState<ImageData>();
    const [explanation, setExplanation] = useState<Explanation>();
    const [showExplanation, setShowExplanationState] = useState<boolean>(false);
    const [showPredictions, setShowPredictions] = useState<boolean>(false);
    const [explanationOpacity, setExplanationOpacity] = useState<number>(50);

    const imageWasUploaded = imageData !== undefined;
    const isLoading = predictionMutation.isPending || explainMutation.isPending;

    const explanations = sortExplanationsByName(explainMutation.data);

    const executeQuickInference = async (file: File, explain: boolean) => {
        if (explain) {
            explainMutation.mutate(
                { file, projectIdentifier },
                {
                    onSuccess: (maps) => {
                        const [firstMap] = sortExplanationsByName(maps);

                        setExplanation(firstMap);
                    },
                }
            );
        } else {
            predictionMutation.mutate({ file, projectIdentifier });
        }
    };

    const setShowExplanation = (value: boolean) => {
        setShowExplanationState(value);

        const alreadyRanWithExplain = explainMutation.isSuccess && !isEmpty(explanation);
        const file = predictionMutation.variables?.file;

        if (file && value && !alreadyRanWithExplain) {
            executeQuickInference(file, value);
        }
    };

    const handleUploadImage = async (files: File[] | FileList) => {
        setExplanation(undefined);
        setShowExplanation(false);

        if (isDisabled) {
            return;
        }

        try {
            const selectedFile = files[0];

            const isSupportedFormat = isValidFileExtension(selectedFile, VALID_IMAGE_TYPES);

            // Quick inference only supports image files with a valid extension
            if (!isSupportedFormat) {
                addNotification({
                    message: `This feature only supports image files. Supported extensions: ${mediaExtensionHandler(
                        VALID_IMAGE_TYPES
                    )}`,
                    type: NOTIFICATION_TYPE.ERROR,
                });

                return;
            }

            await validateMedia(selectedFile);

            const newImageData = isTiffFormat(selectedFile)
                ? await getImageDataFromTiffFile(selectedFile)
                : getImageData(await loadImageFromFile(selectedFile));

            setImageData(newImageData);
            executeQuickInference(selectedFile, false);

            // show annotations if the new image has been uploaded
            !showPredictions && setShowPredictions(true);
        } catch (error: unknown) {
            if (isValidationFailReason(error)) {
                const errorMessage = error.errors.join('\n');

                addNotification({ message: errorMessage, type: NOTIFICATION_TYPE.ERROR });
            }
        }
    };

    const toggleShowPredictions = () => {
        setShowPredictions((v) => !v);
    };

    const annotations = useMemo(() => {
        return predictionMutation.isSuccess && predictionMutation.data && showPredictions
            ? [...predictionMutation.data]
            : [];
    }, [predictionMutation.data, predictionMutation.isSuccess, showPredictions]);

    const dismissWarningCard = () => {
        setDismissWarningCard(true);
    };

    // We want to show a warning card to the user when the inference request is not working
    // We will only do this when the request is not successful yet
    const showWarningCard =
        !warningCardDismissed &&
        ((predictionMutation.failureCount > 0 && !predictionMutation.isSuccess && !predictionMutation.isError) ||
            (explainMutation.failureCount > 0 && !explainMutation.isSuccess && !explainMutation.isError));

    return (
        <QuickInferenceContext.Provider
            value={{
                // TODO: move explanation logic to a different provider
                explanationOpacity,
                setExplanationOpacity,
                explanations,
                explanation,
                setExplanation,
                showExplanation,
                setShowExplanation,

                isDisabled,
                isLoading,
                showPredictions,
                toggleShowPredictions,
                handleUploadImage,
                predictionResult: undefined,
                imageWasUploaded,
                showWarningCard,
                annotations,
                image: imageData,
                dismissWarningCard,
            }}
        >
            {children}
        </QuickInferenceContext.Provider>
    );
};

export const useQuickInference = (): QuickInferenceContextProps => {
    const context = useContext(QuickInferenceContext);

    if (context === undefined) {
        throw new MissingProviderError('useQuickInference', 'QuickInferenceProvider');
    }

    return context;
};
