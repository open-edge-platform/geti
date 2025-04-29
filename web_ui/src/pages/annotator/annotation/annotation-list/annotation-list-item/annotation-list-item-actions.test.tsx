// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render } from '@testing-library/react';

import { getById } from '../../../../../test-utils/utils';
import { AnnotationListItemActions } from './annotation-list-item-actions.component';

describe('Annotations list item actions', () => {
    it('Lock button should be visible when annotation is locked', () => {
        const changeLock = jest.fn();
        const { container } = render(
            <AnnotationListItemActions
                textColor='#000'
                isDisabled={false}
                isLocked={true}
                isHidden={false}
                changeLock={changeLock}
                showAnnotation={jest.fn()}
                annotationId={'test-annotation'}
            />
        );
        const lockOpenButton = getById(container, 'annotation-test-annotation-lock-closed-icon');
        expect(lockOpenButton).toBeInTheDocument();
        lockOpenButton && fireEvent.click(lockOpenButton);
        expect(changeLock).toBeCalled();
    });

    it('Invisible button should be visible when annotation is hidden', () => {
        const mockShowAnnotation = jest.fn();
        const mockAnnotationId = 'test-id';
        const { container } = render(
            <AnnotationListItemActions
                textColor='#000'
                isDisabled={false}
                isLocked={false}
                isHidden={true}
                changeLock={jest.fn()}
                annotationId={mockAnnotationId}
                showAnnotation={mockShowAnnotation}
            />
        );
        const lockOpenButton = getById(container, `annotation-list-item-${mockAnnotationId}-visibility-off`);
        expect(lockOpenButton).toBeInTheDocument();
        lockOpenButton && fireEvent.click(lockOpenButton);
        expect(mockShowAnnotation).toBeCalled();
    });
});
