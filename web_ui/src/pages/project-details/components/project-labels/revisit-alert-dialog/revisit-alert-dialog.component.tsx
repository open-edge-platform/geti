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

import { AlertDialog } from '@adobe/react-spectrum';

import { LabelTreeLabelProps } from '../../../../../core/labels/label-tree-view.interface';
import { useDocsUrl } from '../../../../../hooks/use-docs-url/use-docs-url.hook';
import { LinkNewTab } from '../../../../../shared/components/link-new-tab/link-new-tab.component';
import { DocsUrl } from '../../../../../shared/components/tutorials/utils';

interface RevisitAlertDialogProps {
    flattenNewLabels: LabelTreeLabelProps[];
    save: (shouldRevisit: boolean) => void;
}

export const RevisitAlertDialog = ({ flattenNewLabels, save }: RevisitAlertDialogProps): JSX.Element => {
    const changedLabelsNames = flattenNewLabels.map(({ name }) => `"${name}"`).join(', ');
    const url = useDocsUrl();
    const docsUrl = `${url}${DocsUrl.REVISIT_LABELS}`;
    const learnMore = (
        <>
            <LinkNewTab text={'Learn more'} url={docsUrl}></LinkNewTab> about the revisit status.
        </>
    );
    const promptText = `Some of your already-annotated media might be relevant to the new 
    label${flattenNewLabels.length === 1 ? '' : 's'}: ${changedLabelsNames}. 
    Would you like to assign a "revisit" status to these media? This will help you easily identify and 
    update annotations as required. `;

    return (
        <AlertDialog
            title={`New Label${flattenNewLabels.length === 1 ? '' : 's'} Alert: ${changedLabelsNames}`}
            variant='warning'
            primaryActionLabel='Assign'
            secondaryActionLabel="Don't assign"
            cancelLabel='Cancel'
            onPrimaryAction={() => save(true)}
            onSecondaryAction={() => save(false)}
            UNSAFE_style={{ wordBreak: 'break-word' }}
        >
            {promptText}
            {learnMore}
        </AlertDialog>
    );
};
