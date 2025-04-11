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

import { Label } from '../../../../../core/labels/label.interface';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { LabelHotkey } from './label-hotkey/label-hotkey.component';

interface LabelsHotkeysProps {
    annotationToolContext: AnnotationToolContext;
    labels: Label[];
    hotkeyHandler: (label: Label) => void;
}

export const LabelsHotkeys = ({ annotationToolContext, labels, hotkeyHandler }: LabelsHotkeysProps): JSX.Element => {
    return (
        <>
            {/* filtering out labels with empty/undefined hotkeys we are sure we always have labels with hotkeys */}
            {(labels.filter(({ hotkey }: Label) => !isEmpty(hotkey)) as Required<Label>[]).map(
                (label: Required<Label>) => (
                    <LabelHotkey
                        key={label.id}
                        label={label}
                        annotationToolContext={annotationToolContext}
                        hotkeyHandler={() => hotkeyHandler(label)}
                    />
                )
            )}
        </>
    );
};
