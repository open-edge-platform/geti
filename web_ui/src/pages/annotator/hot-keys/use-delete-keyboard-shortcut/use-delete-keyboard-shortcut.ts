// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';
import { useHotkeys } from 'react-hotkeys-hook';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { HOTKEY_OPTIONS } from '../utils';

export const useDeleteKeyboardShortcut = (
    removeAnnotations: AnnotationScene['removeAnnotations'],
    hasShapePointSelected: AnnotationScene['hasShapePointSelected'],
    annotations: ReadonlyArray<Annotation>
): void => {
    const { hotkeys } = useAnnotatorHotkeys();

    useHotkeys(
        `${hotkeys.delete}, ${hotkeys.deleteSecond}`,
        () => {
            if (!isEmpty(annotations) && !hasShapePointSelected.current) {
                removeAnnotations([...annotations]);
            }
        },
        HOTKEY_OPTIONS,
        [annotations]
    );
};
