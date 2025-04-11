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
