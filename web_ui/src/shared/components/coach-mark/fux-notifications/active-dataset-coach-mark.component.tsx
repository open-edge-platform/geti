// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';
import { createPortal } from 'react-dom';

import { FUX_NOTIFICATION_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useTutorialEnablement } from '../../../hooks/use-tutorial-enablement.hook';
import { CoachMark } from '../coach-mark.component';

export const ActiveDatasetCoachMark = (): JSX.Element => {
    const { isOpen } = useTutorialEnablement(FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET);

    // When the sidebar is collapsed we do not render the dataset-picker so the element with this id
    // is not in the DOM.
    // We had to add this check because of the error occurred during any action with collapsed sidebar
    const datasetPickerDOMElement = document.getElementById('dataset-picker-id') as Element;

    return isOpen && datasetPickerDOMElement ? (
        createPortal(
            <Flex position={'fixed'} width={'100%'} alignItems={'center'} justifyContent={'center'}>
                <CoachMark
                    settingsKey={FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET}
                    styles={{
                        position: 'absolute',
                        width: '450px',
                        left: '-413px',
                        top: '-38px',
                    }}
                />
            </Flex>,
            datasetPickerDOMElement
        )
    ) : (
        <></>
    );
};
