// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
