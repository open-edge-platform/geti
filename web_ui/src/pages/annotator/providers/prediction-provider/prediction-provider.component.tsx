// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, ReactNode, SetStateAction, useContext, useEffect, useState } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';
import { hasEqualId, runWhen } from '@shared/utils';
import { UseQueryResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';

import { Annotation, TaskChainInput } from '../../../../core/annotations/annotation.interface';
import { Explanation } from '../../../../core/annotations/prediction.interface';
import { PredictionResult } from '../../../../core/annotations/services/prediction-service.interface';
import { isAnomalous, isPrediction } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { isAnomalyDomain, isClassificationDomain } from '../../../../core/projects/domains';
import { isKeypointTask } from '../../../../core/projects/utils';
import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { hasValidLabels } from '../../utils';
import { IsPredictionRejected } from '../annotation-threshold-provider/annotation-threshold-provider.component';
import { useTaskChain } from '../task-chain-provider/task-chain-provider.component';
import { useTaskChainOutput } from '../task-chain-provider/use-task-chain-output.hook';
import { getInputsOutputs, getTaskChainInputsOutput } from '../task-chain-provider/utils';
import { useMergeAnnotations } from './use-merge-annotations.hook';
import { usePredictionsRoiQuery } from './use-prediction-roi-query.hook';
import { selectFirstOrNoneFromList, useUpdateVideoPredictionsTimeline } from './utils';

const INFERENCE_MAP_DEFAULT_OPACITY = 50;

export interface PredictionContextProps {
    predictionsRoiQuery: UseQueryResult<PredictionResult, AxiosError>;
    predictionAnnotations: Annotation[];

    // Accept / merge logic
    userAnnotationsExist: boolean;
    enableMergingPredictionsPredicate: () => boolean;
    acceptPrediction: (merge: boolean, isPredictionRejected: IsPredictionRejected) => Promise<void>;

    // Explanations
    explanations: Explanation[];
    selectedExplanation: Explanation | undefined;
    setSelectedExplanation: Dispatch<SetStateAction<Explanation | undefined>>;
    isExplanationVisible: boolean;
    setExplanationVisible: Dispatch<SetStateAction<boolean>>;
}

export interface ExplanationOpacityContextProps {
    explanationOpacity: number;
    setExplanationOpacity: Dispatch<SetStateAction<number>>;
    showOverlapAnnotations: boolean;
    setShowOverlapAnnotations: Dispatch<SetStateAction<boolean>>;
}

const PredictionContext = createContext<PredictionContextProps | undefined>(undefined);
const ExplanationOpacityContext = createContext<ExplanationOpacityContextProps | undefined>(undefined);

// TODO: this should be changed so that it is based on task chain:
// - If there are no inputs, then check if there are any user annotations
// - If there are inputs, check if the selected prediction input exists in user space
// and check if it has annotations
const useUserAnnotationsExists = (
    userAnnotations: ReadonlyArray<Annotation>,
    userInputs: ReadonlyArray<TaskChainInput>,
    selectedInputs: ReadonlyArray<TaskChainInput>
) => {
    const { isSingleDomainProject } = useProject();

    if (isEmpty(userInputs)) {
        // For classification projects we add an empty annotation when loading a media item,
        // since this is not a user provided annotation we should ignore it
        const isSingleClassificationProject = isSingleDomainProject(DOMAIN.CLASSIFICATION);

        const userAnnotationsExist = isSingleClassificationProject
            ? userAnnotations.some(hasValidLabels)
            : !isEmpty(userAnnotations);

        return userAnnotationsExist;
    }

    // Determine if the input have any output
    const relevantUserInputs = userInputs.filter((input) => selectedInputs.some(hasEqualId(input.id)));

    return !isEmpty(relevantUserInputs.flatMap(({ outputs }) => outputs));
};

const useApplyPredictions = (inputs: readonly TaskChainInput[], userAnnotations: ReadonlyArray<Annotation>) => {
    const { tasks, selectedTask, previousTask } = useTask();
    const mergeAnnotations = useMergeAnnotations();

    const { inputs: userInputs } = getInputsOutputs(userAnnotations, tasks, selectedTask);

    const selectedInputs = inputs.filter(({ isSelected }) => isSelected);
    const annotations = useTaskChainOutput(tasks, selectedTask);

    const userAnnotationsExist = useUserAnnotationsExists(userAnnotations, userInputs, selectedInputs);

    const replaceAnnotations = (
        predictionAnnotations: ReadonlyArray<Annotation>,
        newAnnotations: ReadonlyArray<Annotation>
    ) => {
        // HACK: Temporary hack to fix predictions for classification projects
        if (tasks.length === 1 && selectedTask !== null && isClassificationDomain(selectedTask.domain)) {
            // In case of single classification projects we always want to replace the "artificial" annotation we make
            // when loading a new media item, but we want to do it only when we don't have annotation

            if (!isEmpty(newAnnotations.filter(hasValidLabels))) {
                return [...newAnnotations];
            }

            return [...predictionAnnotations];
        }

        // When the user is not in a task chain, or the first task in a task chain,
        // we replace all of its existing annotations as no input is selected
        if (isEmpty(inputs)) {
            return [...predictionAnnotations];
        }

        // replace the user's annotations, filtered by the output of the current input
        const userOutputsForTheseInputs = selectedInputs.flatMap((input) => {
            const userInput = userInputs.find(hasEqualId(input.id));

            if (userInput === undefined) {
                return [];
            }

            return userInput.outputs;
        });

        // Remove all user's annotations that belong to this input
        const filteredUserAnnotations = newAnnotations.filter((annotation) => {
            return !userOutputsForTheseInputs.some(hasEqualId(annotation.id));
        });

        // Always include the selected inputs into the merged annotations,
        // we don't want their associated outputs to be stored into the annotation scene
        const missingInputAnnotations = selectedInputs.map(({ outputs, ...annotation }) => annotation);

        // For detection -> classification tasks we need to merge the prediction annotations with the user's annotations
        // as the prediction annotations from classification replace the labels on the detection annotations
        return mergeAnnotations(predictionAnnotations, [...filteredUserAnnotations, ...missingInputAnnotations]);
    };

    const applyPredictions = (
        merge: boolean,
        predictions: Annotation[],
        predictionsInputs: readonly TaskChainInput[],
        isPredictionRejected: IsPredictionRejected = () => false
    ) => {
        // Only merge annotations that are not rejected (via the score filter),
        // and that are in the currently selected input's outputs
        const filteredPredictionInputs = predictionsInputs.filter((input) => selectedInputs.some(hasEqualId(input.id)));
        const acceptedPredictions = predictions.filter((prediction) => {
            if (isPredictionRejected(prediction)) {
                return false;
            }

            if (isNil(previousTask)) {
                return true;
            }

            return filteredPredictionInputs.some(({ outputs }) => outputs.some(hasEqualId(prediction.id)));
        });

        if (merge) {
            // Always include the selected inputs into the merged annotations,
            // we don't want their associated outputs to be stored into the annotation scene
            const missingInputAnnotations = filteredPredictionInputs.map(({ outputs, ...annotation }) => annotation);

            return mergeAnnotations(acceptedPredictions, [...userAnnotations, ...missingInputAnnotations]);
        }

        return replaceAnnotations(acceptedPredictions, userAnnotations);
    };

    const enableMergingPredictionsPredicate = () => {
        // For anomaly and classification projects, sometimes merging will have
        // the same effect as replacing annotations.
        // In this case we don't want to show the user a dialog asking them to merge,
        // instead we will always replace the annotations
        if (tasks.length === 1 && selectedTask !== null) {
            if (isClassificationDomain(selectedTask.domain)) {
                return false;
            }

            if (isAnomalyDomain(selectedTask.domain)) {
                // Always replace global annotations for anomaly projects

                if (userAnnotations.length <= 1) {
                    return false;
                }

                // Only allow merging if the user and predicted annotations are both anomalous
                return userAnnotations.every(isAnomalousAnnotation) && annotations.every(isAnomalousAnnotation);
            }

            if (isKeypointTask(tasks[0])) {
                return false;
            }
        }

        return !isEmpty(userAnnotations);
    };

    return {
        applyPredictions,
        userAnnotationsExist,
        userSceneSelectedInputs: selectedInputs,
        enableMergingPredictionsPredicate,
    };
};

interface PredictionProviderProps {
    children: ReactNode;
    settings: UseSettings<UserProjectSettings>;
    explanations: Explanation[];
    userAnnotationScene: AnnotationScene;
    initPredictions: undefined | readonly Annotation[];
}

const selectAnnotations = (annotations: readonly Annotation[], inputs: TaskChainInput[]) =>
    annotations.map((annotation) => {
        const isSelected = Boolean(inputs.find(hasEqualId(annotation.id)));

        return {
            ...annotation,
            isSelected,
        };
    });

const isAnomalousAnnotation = ({ labels }: Annotation) => labels.every(isAnomalous);

export const ExplanationOpacityProvider = ({ children }: { children: ReactNode }) => {
    const [explanationOpacity, setExplanationOpacity] = useState(INFERENCE_MAP_DEFAULT_OPACITY);
    const [showOverlapAnnotations, setShowOverlapAnnotations] = useState(false);

    return (
        <ExplanationOpacityContext.Provider
            value={{ explanationOpacity, setExplanationOpacity, showOverlapAnnotations, setShowOverlapAnnotations }}
        >
            {children}
        </ExplanationOpacityContext.Provider>
    );
};

export const PredictionProvider = ({
    children,
    settings,
    initPredictions,
    userAnnotationScene,
    explanations: initExplanations,
}: PredictionProviderProps): JSX.Element => {
    const { inputs } = useTaskChain();
    const { isActiveLearningMode } = useAnnotatorMode();
    const { isTaskChainSecondTask, isTaskChainDomainSelected, tasks, selectedTask } = useTask();

    const [explanations, setExplanations] = useState<Explanation[]>(initExplanations);
    const userAnnotations = useTaskChainOutput(tasks, selectedTask);
    const [rawPredictions, setRawPredictions] = useState(initPredictions ?? []);
    const [isExplanationVisible, setExplanationVisible] = useState<boolean>(false);
    const [selectedExplanation, setSelectedExplanation] = useState<Explanation | undefined>(undefined);
    const getPredictionOutputs = getTaskChainInputsOutput(tasks, selectedTask);

    const isPredictionMode = !isActiveLearningMode;
    const [selectedInput] = inputs.filter(({ isSelected }) => isSelected);
    const [predictionAnnotations, predictionsInputs] = getPredictionOutputs(rawPredictions);
    const settingsConfig = getSettingsOfType(settings.config, FEATURES_KEYS);

    const initialPredictionsConfig = settingsConfig[FEATURES_KEYS.INITIAL_PREDICTION];

    useEffect(() => {
        if (initPredictions !== undefined) {
            setRawPredictions(initPredictions);
        }
    }, [initPredictions]);

    useEffect(() => {
        setExplanations(initExplanations);
        setSelectedExplanation(selectFirstOrNoneFromList(initExplanations));
    }, [initExplanations]);

    useEffect(() => {
        setSelectedExplanation(selectFirstOrNoneFromList(explanations));
    }, [explanations]);

    useEffect(() => {
        if (!selectedInput?.id) {
            return;
        }
        const matchMap = explanations.find(({ roi }) => roi.id === selectedInput.id);

        matchMap && setSelectedExplanation(matchMap);
    }, [explanations, selectedInput?.id]);

    const runWhenNotDrawing = runWhen<PredictionResult>(() => !userAnnotationScene.isDrawing || isPredictionMode);
    const updateVideoPredictionsTimeline = useUpdateVideoPredictionsTimeline();

    const { userAnnotationsExist, userSceneSelectedInputs, applyPredictions, enableMergingPredictionsPredicate } =
        useApplyPredictions(inputs, userAnnotationScene.annotations);

    const acceptPrediction = async (merge = false, isPredictionRejected: IsPredictionRejected) => {
        const newAnnotations = applyPredictions(merge, predictionAnnotations, predictionsInputs, isPredictionRejected);

        userAnnotationScene.replaceAnnotations(newAnnotations);
    };

    const getNewPredictionAnnotations = (selectedRawPredictions: Annotation[]): Annotation[] => {
        const [iPredictionAnnotations, iPredictionsInputs] = getPredictionOutputs(selectedRawPredictions);

        return applyPredictions(false, iPredictionAnnotations, iPredictionsInputs);
    };

    const isPredictionModeOrInitialPredictions = isPredictionMode ? true : initialPredictionsConfig.isEnabled;
    const isSuggestPredictionsEnabled = settings.config[FEATURES_KEYS.INITIAL_PREDICTION].isEnabled;

    const isPredictionsQueryEnabled =
        isSuggestPredictionsEnabled && isTaskChainSecondTask && isPredictionModeOrInitialPredictions;

    // If we are at task chain's second task, get prediction for the selected ROI input
    const predictionsRoiQuery = usePredictionsRoiQuery({
        selectedInput,
        taskId: String(selectedTask?.id),
        enabled: isPredictionsQueryEnabled,
        onSuccess: runWhenNotDrawing(({ annotations: newRawPredictions, maps: newMaps }: PredictionResult) => {
            const selectedPredictions = selectAnnotations(newRawPredictions, userSceneSelectedInputs);

            if (isEmpty(userAnnotations)) {
                const newAnnotations = getNewPredictionAnnotations(selectedPredictions);

                userAnnotationScene.replaceAnnotations(newAnnotations);
            }

            if (isTaskChainDomainSelected(DOMAIN.CLASSIFICATION)) {
                const newAnnotations = getNewPredictionAnnotations(selectedPredictions);

                const newPrediction = newAnnotations.find(hasEqualId(selectedInput.id));
                const selectedInputLabels = [...selectedInput.labels];
                const isSingleLabelOrPrediction =
                    selectedInputLabels.length === 1 || isPrediction(selectedInputLabels.at(-1));

                const canUpdatePrediction = isSingleLabelOrPrediction && newPrediction;

                canUpdatePrediction && userAnnotationScene.updateAnnotation(newPrediction);
            }

            setExplanations(newMaps);
            setRawPredictions(selectedPredictions);

            // Optionally update video timeline predictions
            updateVideoPredictionsTimeline(newRawPredictions);
        }),
    });

    return (
        <PredictionContext.Provider
            value={{
                predictionsRoiQuery,
                predictionAnnotations,

                // Accept / merge logic
                userAnnotationsExist,
                acceptPrediction,
                enableMergingPredictionsPredicate,

                // Explanations
                explanations,
                selectedExplanation,
                setSelectedExplanation,
                isExplanationVisible,
                setExplanationVisible,
            }}
        >
            <ExplanationOpacityProvider>{children}</ExplanationOpacityProvider>
        </PredictionContext.Provider>
    );
};

export const usePrediction = (): PredictionContextProps => {
    const context = useContext(PredictionContext);

    if (context === undefined) {
        throw new MissingProviderError('usePrediction', 'PredictionProvider');
    }

    return context;
};

export const useExplanationOpacity = (): ExplanationOpacityContextProps => {
    const context = useContext(ExplanationOpacityContext);

    if (context === undefined) {
        throw new MissingProviderError('useExplanationOpacity', 'ExplanationOpacityProvider');
    }

    return context;
};
