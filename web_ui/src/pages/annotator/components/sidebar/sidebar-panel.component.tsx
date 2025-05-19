// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MutableRefObject, ReactNode, useRef, useState } from 'react';

import { DimensionValue, Flex, Overlay, View } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { Responsive, StyleProps } from '@react-types/shared';
import { useOverlay } from 'react-aria';

import { Datasets, Edit, Manifest } from '../../../../assets/icons';
import { QuietToggleButton } from '../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { AnnotationListContainer } from '../../annotation/annotation-list/annotation-list-container/annotation-list-container.component';
import { AnnotationListCounting } from './annotations/annotation-list-counting.component';
import { AnnotationsHeader } from './annotations/annotations-header.component';
import { DatasetAccordion } from './dataset/dataset-accordion.component';
import { SidebarCommonProps } from './sidebar.interface';

import classes from './sidebar-panel.module.scss';

type SidebarPanelProps = SidebarCommonProps;

interface OverlayPanelProps extends StyleProps {
    icon: JSX.Element;
    children: ReactNode;
    ariaLabel?: string;
    padding?: Responsive<DimensionValue> | undefined;
}

const OverlayPanel = ({ icon, children, ariaLabel = '', ...props }: OverlayPanelProps) => {
    const overlayRef = useRef(null);
    const container = useRef(null);
    const dialogState = useOverlayTriggerState({});
    const [panelAnimationClasses, setPanelAnimationClasses] = useState([classes.panel]);

    useOverlay(
        {
            isDismissable: true,
            shouldCloseOnBlur: false,
            isOpen: dialogState.isOpen,
            onClose: dialogState.close,
        },
        container
    );

    return (
        <>
            <QuietToggleButton onPress={dialogState.toggle} isSelected={dialogState.isOpen} aria-label={ariaLabel}>
                {icon}
            </QuietToggleButton>

            <Overlay
                nodeRef={overlayRef as unknown as MutableRefObject<HTMLElement>}
                isOpen={dialogState.isOpen}
                onExiting={() =>
                    setPanelAnimationClasses((prev) => prev.filter((name) => name !== classes.panelOpened))
                }
                onEntering={() => setPanelAnimationClasses((prev) => [...prev, classes.panelOpened])}
            >
                <div ref={container}>
                    <View
                        data-testid={`${ariaLabel} overlay`}
                        gridColumn='size-150 1fr size-150'
                        UNSAFE_className={panelAnimationClasses.join(' ')}
                        {...props}
                    >
                        {children}
                    </View>
                </div>
            </Overlay>
        </>
    );
};

export const SidebarPanel = ({
    showDatasetPanel,
    showCountingPanel,
    showAnnotationPanel,
    annotationToolContext,
    setDatasetViewMode,
    datasetViewMode,
}: SidebarPanelProps) => {
    return (
        <View
            height='100%'
            padding='size-100'
            position='relative'
            backgroundColor='gray-200'
            data-testid='sidebar-panel'
        >
            <Flex height='100%' direction='column' justifyContent='stretch'>
                {showAnnotationPanel && (
                    <OverlayPanel icon={<Edit />} padding='size-100' ariaLabel='annotation list'>
                        <Flex direction={'column'} height={'100%'}>
                            <AnnotationsHeader />
                            <AnnotationListContainer />
                        </Flex>
                    </OverlayPanel>
                )}

                {showCountingPanel && (
                    <OverlayPanel icon={<Manifest />} ariaLabel='annotation list count'>
                        <AnnotationListCounting annotationToolContext={annotationToolContext} />
                    </OverlayPanel>
                )}

                {showDatasetPanel && (
                    <OverlayPanel icon={<Datasets />} ariaLabel='dataset accordion'>
                        <DatasetAccordion viewMode={datasetViewMode} setViewMode={setDatasetViewMode} />
                    </OverlayPanel>
                )}
            </Flex>
        </View>
    );
};
