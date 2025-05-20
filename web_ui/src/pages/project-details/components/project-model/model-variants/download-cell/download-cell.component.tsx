// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButtonProps } from '@geti/ui';
import { DownloadIcon } from '@geti/ui/icons';

import { ButtonWithSpectrumTooltip } from '../../../../../../shared/components/button-with-tooltip/button-with-tooltip.component';
import { idMatchingFormat } from '../../../../../../test-utils/id-utils';

interface DownloadCellInterface extends ActionButtonProps {
    id: string;
    onDownload: () => void;
}

export const DownloadCell = ({ id, onDownload, ...props }: DownloadCellInterface): JSX.Element => {
    return (
        <ButtonWithSpectrumTooltip
            isQuiet
            id={`${idMatchingFormat(id)}-download-model-button`}
            onPress={onDownload}
            tooltip={'Download model'}
            isClickable
            {...props}
        >
            <DownloadIcon id={'download-model-id'} />
        </ButtonWithSpectrumTooltip>
    );
};
