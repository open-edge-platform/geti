// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedLabel } from '../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { getById } from '../../../test-utils/utils';
import { LabelColorThumb } from './label-color-thumb.component';

describe('LabelColorThumb', () => {
    it('render labels color', async () => {
        const noObjectLabel = getMockedLabel({ id: '123', color: '#000', name: 'test' });
        const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

        expect(getById(container, noObjectLabel.id)).toBeInTheDocument();
    });

    describe('empty labels', () => {
        it('No object', async () => {
            const noObjectLabel = getMockedLabel({
                id: '123',
                color: '#000',
                name: 'No object',
                group: 'No object',
                isEmpty: true,
            });
            const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

            expect(getById(container, noObjectLabel.id)).toBeNull();
        });

        it('Empty', async () => {
            const noObjectLabel = getMockedLabel({
                id: '123',
                color: '#000',
                name: 'Empty',
                group: 'Empty',
                isEmpty: true,
            });
            const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

            expect(getById(container, noObjectLabel.id)).toBeNull();
        });

        it('No class', async () => {
            const noObjectLabel = getMockedLabel({
                id: '123',
                color: '#000',
                name: 'No class',
                group: 'No class',
                isEmpty: true,
            });
            const { container } = render(<LabelColorThumb id={'123'} label={noObjectLabel} />);

            expect(getById(container, noObjectLabel.id)).toBeNull();
        });
    });
});
