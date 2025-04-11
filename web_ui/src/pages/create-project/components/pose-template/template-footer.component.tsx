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

import { Content, Flex, View } from '@adobe/react-spectrum';

import { Divider } from '../../../../shared/components/divider/divider.component';
import { ZoomLevel } from '../../../annotator/components/footer/zoom-level/zoom-level.component';
import { useZoom } from '../../../annotator/zoom/zoom-provider.component';

export const TemplateFooter = () => {
    const { zoomState } = useZoom();

    return (
        <View backgroundColor={'gray-100'}>
            <Flex gap={'size-200'} gridArea={'footer'} justifyContent={'end'}>
                <Divider orientation={'vertical'} size={'S'} height={'size-300'} margin={'auto 0px'} />
                <Content>
                    <ZoomLevel zoom={zoomState.zoom} />
                </Content>
            </Flex>
        </View>
    );
};
