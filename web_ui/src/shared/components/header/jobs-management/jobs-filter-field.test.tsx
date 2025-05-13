// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { JobsFilterField, JobsFilterFieldProps } from './jobs-filter-field.component';

describe('jobs-filter-field', (): void => {
    const onLoadMore = jest.fn();
    const onSelectionChange = jest.fn();

    let clientHeightSpy: jest.MockInstance<number, []>;
    let scrollHeightSpy: jest.MockInstance<number, []>;

    beforeEach(() => {
        scrollHeightSpy = jest.spyOn(window.HTMLElement.prototype, 'scrollHeight', 'get').mockImplementation(() => 32);
        clientHeightSpy = jest
            .spyOn(window.HTMLElement.prototype, 'clientHeight', 'get')
            .mockImplementationOnce((): number => 0)
            .mockImplementation(function (): number {
                // @ts-expect-error use of this
                return this.getAttribute('role') === 'listbox' ? 100 : 40;
            });
    });

    afterEach(() => {
        clientHeightSpy.mockRestore();
        scrollHeightSpy.mockRestore();
        jest.spyOn(window.HTMLElement.prototype, 'clientHeight', 'get').mockImplementation((): number => 1000);
    });

    const renderComponent = async (customProps?: Partial<JobsFilterFieldProps>): Promise<void> => {
        render(
            <JobsFilterField
                onSelectionChange={onSelectionChange}
                loadMore={onLoadMore}
                ariaLabel={'Test aria label'}
                value={'test_value_1'}
                options={[
                    { key: 'test_value', name: 'Test Value' },
                    { key: 'test_value_1', name: 'Test Value 1' },
                    { key: 'test_value_2', name: 'Test Value 2' },
                ]}
                {...customProps}
            />
        );
    };

    it('should properly render base component', async (): Promise<void> => {
        await renderComponent();
        expect(screen.getByRole('button', { name: /Test aria label/ })).toHaveTextContent('Test Value 1');
    });

    it('should render suggestion panel on click', async (): Promise<void> => {
        await renderComponent();

        fireEvent.click(screen.getByRole('button', { name: /Test aria label/ }));

        expect(screen.getAllByRole('option')).toHaveLength(3);

        expect(screen.getByRole('option', { name: 'Test Value' })).toBeVisible();
        expect(screen.getByRole('option', { name: 'Test Value 1' })).toBeVisible();
        expect(screen.getByRole('option', { name: 'Test Value 2' })).toBeVisible();
    });

    it('should trigger onSelectionChange event with selected key', async (): Promise<void> => {
        await renderComponent();
        fireEvent.click(screen.getByRole('button', { name: /Test aria label/ }));
        fireEvent.click(screen.getByRole('option', { name: 'Test Value 2' }));
        expect(onSelectionChange).toHaveBeenCalledWith('test_value_2');
    });
});
