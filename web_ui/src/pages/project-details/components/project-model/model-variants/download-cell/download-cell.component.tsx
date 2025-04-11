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

import { DownloadIcon } from '../../../../../../assets/icons';
import { ButtonWithSpectrumTooltip } from '../../../../../../shared/components/button-with-tooltip/button-with-tooltip.component';
import { ActionButtonProps } from '../../../../../../shared/components/button/button.component';
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
