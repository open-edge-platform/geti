// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
