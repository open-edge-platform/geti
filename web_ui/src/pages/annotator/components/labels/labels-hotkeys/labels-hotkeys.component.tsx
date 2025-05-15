// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isEmpty } from 'lodash-es';

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
