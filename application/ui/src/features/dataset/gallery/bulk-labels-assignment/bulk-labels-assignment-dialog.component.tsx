// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    dimensionValue,
    Divider,
    Flex,
    Heading,
    Text,
} from '@geti-ui/ui';
import { Info } from '@geti-ui/ui/icons';
import { useProject } from 'hooks/api/project.hook';
import { isEmpty } from 'lodash-es';
import { useTranslation } from 'react-i18next';

import { useProjectLabelsWithEmptyLabel } from '../../../../shared/annotator/labels';
import { isImage } from '../../../../shared/media-item-utils';
import { isMultiLabelClassificationTask } from '../../../project/task-type-guards';
import { useMediaUpload } from '../../api/use-media-upload';
import { useBulkAssignLabel } from './api/use-bulk-assign-label';
import { LabelsList } from './labels-list/labels-list.component';

type BulkLabelsAssignmentDialogContentProps = {
    onClose: () => void;
    onSkip: () => void;
    isSkipPending: boolean;
    onContinue: (labelIds: string[]) => Promise<void>;
    isContinuePending: boolean;
    isMultiLabelClassification: boolean;
};

const BulkLabelsAssignmentDialogContent = ({
    onClose,
    onSkip,
    onContinue,
    isSkipPending,
    isContinuePending,
    isMultiLabelClassification,
}: BulkLabelsAssignmentDialogContentProps) => {
    const projectLabels = useProjectLabelsWithEmptyLabel();
    const { t } = useTranslation();

    const [selectedLabels, setSelectedLabels] = useState<Set<string>>(() => new Set([]));

    const isContinueDisabled = selectedLabels.size === 0 || isContinuePending;

    const handleContinue = async () => {
        await onContinue(Array.from(selectedLabels));
    };

    return (
        <Dialog height={'65vh'}>
            <Heading>{t('dataset.labelAssignmentHeading')}</Heading>
            <Divider />
            <Content>
                <Flex direction={'column'} gap={'size-100'} height={'100%'} minHeight={0}>
                    <Text>{t('dataset.chooseLabelsUploadText')}</Text>
                    <Divider size={'S'} marginY={'size-100'} />
                    <LabelsList
                        ariaLabel={t('dataset.labelsToAssignAriaLabel')}
                        labels={projectLabels}
                        selectedLabels={selectedLabels}
                        onSelectedLabelsChange={setSelectedLabels}
                        isMultiple={isMultiLabelClassification}
                    />
                    <Flex gap={'size-50'}>
                        <Info />
                        <Text UNSAFE_style={{ lineHeight: dimensionValue('size-225') }}>
                            {t('dataset.imagesOnlyNote')}
                        </Text>
                    </Flex>
                </Flex>
            </Content>
            <ButtonGroup>
                <Button variant={'secondary'} onPress={onClose}>
                    {t('dataset.cancelUploadButton')}
                </Button>
                <Button variant={'secondary'} onPress={onSkip} isPending={isSkipPending} isDisabled={isSkipPending}>
                    {t('dataset.skipButton')}
                </Button>
                <Button
                    variant={'accent'}
                    onPress={handleContinue}
                    isDisabled={isContinueDisabled}
                    isPending={isContinuePending}
                >
                    {t('dataset.continueButton')}
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};

type BulkLabelsAssignmentDialogProps = {
    files: File[];
    onClose: () => void;
};

export const BulkLabelsAssignmentDialog = ({ files, onClose }: BulkLabelsAssignmentDialogProps) => {
    const isVisible = !isEmpty(files);
    const { data: project } = useProject();
    const isMultiLabelClassification = isMultiLabelClassificationTask(project.task);
    const { uploadMedia, uploadProgress } = useMediaUpload();

    const bulkAssignLabel = useBulkAssignLabel();

    const handleSkip = async () => {
        void uploadMedia(files);
        onClose();
    };

    const handleAccept = async (labelIds: string[]) => {
        const mediaItems = await uploadMedia(files);
        const mediaItemImages = mediaItems.filter(isImage);

        await bulkAssignLabel.mutate(
            mediaItemImages.map(({ id }) => id),
            labelIds
        );

        onClose();
    };

    return (
        <DialogContainer onDismiss={onClose}>
            {isVisible && (
                <BulkLabelsAssignmentDialogContent
                    onClose={onClose}
                    onSkip={handleSkip}
                    onContinue={handleAccept}
                    isContinuePending={uploadProgress.isUploading || bulkAssignLabel.isPending}
                    isSkipPending={uploadProgress.isUploading}
                    isMultiLabelClassification={isMultiLabelClassification}
                />
            )}
        </DialogContainer>
    );
};
