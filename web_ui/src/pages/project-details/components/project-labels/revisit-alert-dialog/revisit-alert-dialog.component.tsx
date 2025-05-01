// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AlertDialog } from '@adobe/react-spectrum';
import { LinkNewTab } from '@shared/components/link-new-tab/link-new-tab.component';
import { DocsUrl } from '@shared/components/tutorials/utils';

import { LabelTreeLabelProps } from '../../../../../core/labels/label-tree-view.interface';
import { useDocsUrl } from '../../../../../hooks/use-docs-url/use-docs-url.hook';

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
