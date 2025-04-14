// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { AnnotationSceneState } from '../../../../core/media/media-filter.interface';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ANNOTATION_SCENE_OPTIONS } from '../../utils';
import {
    anomalyItems,
    MediaFilterValueAnnotationSceneState,
} from './media-filter-value-annotation-scene-state.component';

describe('MediaFilterValueAnnotationSceneState', () => {
    const onSelectionChange = jest.fn();

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('allows to select the Annotated and call onSelectionChange', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                value=''
                isAnomalyProject={false}
                isTaskChainProject={true}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));
        fireEvent.click(screen.getByRole('menuitemradio', { hidden: true, name: 'Annotated' }));

        expect(onSelectionChange).toHaveBeenCalledWith(AnnotationSceneState.ANNOTATED);
    });

    it('render all option list', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                value=''
                isAnomalyProject={false}
                isTaskChainProject={true}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));
        ANNOTATION_SCENE_OPTIONS.forEach(({ text }) => {
            expect(screen.queryByRole('menuitemradio', { hidden: true, name: text })).toBeInTheDocument();
        });
    });

    it('render valid options for anomaly project', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                value=''
                isAnomalyProject={true}
                isTaskChainProject={false}
                onSelectionChange={onSelectionChange}
            />
        );

        const anomalyOptions = ANNOTATION_SCENE_OPTIONS.filter(({ key }) => anomalyItems.includes(key));
        const otherOptions = ANNOTATION_SCENE_OPTIONS.filter(({ key }) => !anomalyItems.includes(key));

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));

        anomalyOptions.forEach(({ text }) => {
            expect(screen.queryByRole('menuitemradio', { hidden: true, name: text })).toBeInTheDocument();
        });

        otherOptions.forEach(({ text }) => {
            expect(screen.queryByRole('menuitemradio', { hidden: true, name: text })).not.toBeInTheDocument();
        });
    });

    it('render valid options for single task project', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                value=''
                isAnomalyProject={false}
                isTaskChainProject={false}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));

        expect(screen.queryAllByRole('menuitemradio')).toHaveLength(3);

        expect(screen.queryByText('Partially annotated')).not.toBeInTheDocument();
    });

    it('Check displayed values', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                value=''
                isAnomalyProject={false}
                isTaskChainProject={true}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));
        expect(screen.getByRole('menuitemradio', { name: 'Unannotated' }).getAttribute('data-key')).toBe('NONE');
        expect(screen.getByRole('menuitemradio', { name: 'Annotated' }).getAttribute('data-key')).toBe('ANNOTATED');
        expect(screen.getByRole('menuitemradio', { name: 'Partially annotated' }).getAttribute('data-key')).toBe(
            'PARTIALLY_ANNOTATED'
        );
        expect(screen.getByRole('menuitemradio', { name: 'Revisit' }).getAttribute('data-key')).toBe('TO_REVISIT');
    });

    it('Check if Unannotated is sending NONE', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                value=''
                isAnomalyProject={false}
                isTaskChainProject={true}
                onSelectionChange={onSelectionChange}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));
        fireEvent.click(screen.getByRole('menuitemradio', { hidden: true, name: 'Unannotated' }));

        expect(onSelectionChange).toHaveBeenCalledWith('NONE');
    });

    it('allows selecting multiple statuses', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                // Note: when multi selection is turned on we expect to receive an array
                value={[AnnotationSceneState.ANNOTATED]}
                isAnomalyProject={false}
                isTaskChainProject={true}
                onSelectionChange={onSelectionChange}
                isMultiselection
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));
        fireEvent.click(screen.getByRole('menuitemcheckbox', { hidden: true, name: 'Partially annotated' }));

        expect(onSelectionChange).toHaveBeenCalledWith([
            AnnotationSceneState.ANNOTATED,
            AnnotationSceneState.PARTIALLY_ANNOTATED,
        ]);
    });

    // This is more a bug than a feature, but at the moment this is necessary
    // until we fix a syncing bug that is inside the MediaFilter component
    it('accepts a single string as input when multi selection is turned on', async () => {
        render(
            <MediaFilterValueAnnotationSceneState
                // Note: when multi selection is turned on we expect to receive an array
                value={AnnotationSceneState.ANNOTATED}
                isAnomalyProject={false}
                isTaskChainProject={true}
                onSelectionChange={onSelectionChange}
                isMultiselection
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /media-filter-annotation-scene-state/i }));
        fireEvent.click(screen.getByRole('menuitemcheckbox', { hidden: true, name: 'Partially annotated' }));

        expect(onSelectionChange).toHaveBeenCalledWith([
            AnnotationSceneState.ANNOTATED,
            AnnotationSceneState.PARTIALLY_ANNOTATED,
        ]);
    });
});
