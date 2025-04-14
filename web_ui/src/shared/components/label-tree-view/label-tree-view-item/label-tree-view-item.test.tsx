// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, within } from '@testing-library/dom';

import { LabelItemEditionState, LabelItemType, LabelTreeItem } from '../../../../core/labels/label-tree-view.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { LabelTreeViewItem, LabelTreeViewItemProps } from './label-tree-view-item.component';

const checkNumberOfMenuActions = (itemId: string, type: 'label' | 'group', quantity: number) => {
    expect(within(screen.getByTestId(`tree-item-menu-${itemId}-${type}`)).queryAllByRole('button')).toHaveLength(
        quantity
    );
};

const saveHandler = jest.fn();
const deleteItemHandler = jest.fn();

describe('LabelTreeViewItem', () => {
    const domains = [DOMAIN.DETECTION];

    const defaultItemProps: Omit<LabelTreeViewItemProps, 'item'> = {
        save: jest.fn(),
        addChild: jest.fn(),
        projectLabels: [],
        deleteItem: jest.fn(),
        isEditable: true,
        isMixedRelation: false,
        isCreationInNewProject: false,
        domains,
        validationErrors: {},
        setValidationError: jest.fn(),
    };

    it('Idle Group has 2 actions: to add label or delete group', async () => {
        const mockedGroup = getMockedTreeGroup({ name: 'Test group' });
        render(<LabelTreeViewItem {...defaultItemProps} item={mockedGroup} />);

        expect(screen.getByRole('button', { name: 'add child label button' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
        expect(screen.getAllByRole('button')).toHaveLength(2);
    });

    it('Click on tree item - actions are visible', async () => {
        const mockedLabel = getMockedTreeLabel({ name: 'Test label' });

        render(
            <LabelTreeViewItem
                item={mockedLabel}
                save={saveHandler}
                addChild={jest.fn()}
                deleteItem={jest.fn()}
                projectLabels={[]}
                isEditable={true}
                domains={[DOMAIN.CLASSIFICATION]}
                isMixedRelation={true}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        fireEvent.click(screen.getByRole('listitem', { name: 'label item Test label' }));
        expect(screen.getByRole('button', { name: 'add child group button' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
    });

    it('Click on tree item - actions are visible - click again to hide item actions', async () => {
        const mockedLabel = getMockedTreeLabel({ name: 'Test label', id: 'mocked-label-id' });

        render(
            <LabelTreeViewItem
                item={mockedLabel}
                save={saveHandler}
                addChild={jest.fn()}
                deleteItem={deleteItemHandler}
                projectLabels={[]}
                isEditable={true}
                domains={domains}
                isMixedRelation={true}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        const item = screen.getByRole('listitem', { name: 'label item Test label' });

        fireEvent.click(item);
        fireEvent.click(item);

        expect(screen.queryByTestId('mocked-label-id-add child group button')).not.toBeInTheDocument();
        expect(screen.queryByTestId('mocked-label-id-edit label button')).not.toBeInTheDocument();
        expect(screen.queryByTestId('mocked-label-id-delete')).not.toBeInTheDocument();
    });
});

describe('Delete group', () => {
    const domains = [DOMAIN.DETECTION];

    const defaultItemProps: Omit<LabelTreeViewItemProps, 'item'> = {
        save: saveHandler,
        addChild: jest.fn(),
        projectLabels: [],
        isCreationInNewProject: false,
        deleteItem: deleteItemHandler,
        domains,
        isEditable: true,
        isMixedRelation: false,
        validationErrors: {},
        setValidationError: jest.fn(),
    };

    it('Remove group from new tree', async () => {
        const item = getMockedTreeGroup({ name: 'test', state: LabelItemEditionState.IDLE });

        render(<LabelTreeViewItem {...defaultItemProps} item={item} isCreationInNewProject />);

        fireEvent.click(screen.getByRole('button', { name: 'delete' }));
        expect(deleteItemHandler).toHaveBeenCalledWith(item);
    });

    it('Remove new group', async () => {
        const item = getMockedTreeGroup({ name: 'test', state: LabelItemEditionState.NEW });

        render(<LabelTreeViewItem {...defaultItemProps} item={item} />);

        fireEvent.click(screen.getByRole('button', { name: 'delete' }));
        expect(deleteItemHandler).toHaveBeenCalledWith(item);
    });

    it('Remove group', async () => {
        const item = getMockedTreeGroup({ name: 'test', state: LabelItemEditionState.IDLE });

        render(<LabelTreeViewItem {...defaultItemProps} item={item} isCreationInNewProject={false} />);

        fireEvent.click(screen.getByRole('button', { name: 'delete' }));
        expect(saveHandler).toHaveBeenCalledWith({ ...item, state: LabelItemEditionState.IDLE }, item.id);
    });

    it('Remove group with children', async () => {
        const children = [getMockedTreeLabel({ name: 'child 1' })];
        const item = getMockedTreeGroup({ name: 'test', state: LabelItemEditionState.IDLE, children });

        render(<LabelTreeViewItem {...defaultItemProps} item={item} isCreationInNewProject={false} />);

        fireEvent.click(screen.getByRole('button', { name: 'delete' }));

        expect(saveHandler).toHaveBeenCalledWith(
            { ...item, children: children.map((child) => ({ ...child, state: LabelItemEditionState.REMOVED })) },
            item.id
        );
    });
});

describe('Delete labels', () => {
    const domains = [DOMAIN.DETECTION];

    it('Remove label from new tree', async () => {
        const item = getMockedTreeLabel({ name: 'test' });

        render(
            <LabelTreeViewItem
                item={item}
                save={saveHandler}
                addChild={jest.fn()}
                deleteItem={deleteItemHandler}
                projectLabels={[]}
                isCreationInNewProject={true}
                domains={domains}
                isEditable={true}
                isMixedRelation={false}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'delete' }));
        expect(deleteItemHandler).toHaveBeenCalledWith(item);
    });

    it('Remove new label', async () => {
        const item = getMockedTreeLabel({ name: 'test', state: LabelItemEditionState.NEW });

        render(
            <LabelTreeViewItem
                item={item}
                save={saveHandler}
                addChild={jest.fn()}
                deleteItem={deleteItemHandler}
                projectLabels={[]}
                isCreationInNewProject={false}
                domains={domains}
                isEditable={true}
                isMixedRelation={false}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'delete' }));
        expect(deleteItemHandler).toHaveBeenCalledWith(item);
    });

    it('Remove label', async () => {
        const item = getMockedTreeLabel({ name: 'test', state: LabelItemEditionState.IDLE });

        render(
            <LabelTreeViewItem
                item={item}
                save={saveHandler}
                addChild={jest.fn()}
                projectLabels={[]}
                deleteItem={jest.fn()}
                isCreationInNewProject={false}
                domains={domains}
                isEditable={true}
                isMixedRelation={false}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'delete' }));
        expect(saveHandler).toHaveBeenCalledWith({ ...item, state: LabelItemEditionState.REMOVED }, item.id);
    });
});

describe('Open close nodes', () => {
    const domains = [DOMAIN.DETECTION];

    const addChildHandler = jest.fn();

    const item = getMockedTreeGroup({
        name: 'animal',
        children: [
            getMockedTreeLabel({
                name: 'cat',
                id: 'cat-label',
                children: [
                    getMockedTreeGroup({
                        name: 'type',
                        children: [getMockedTreeLabel({ name: 'cute' }), getMockedTreeLabel({ name: 'lazy' })],
                    }),
                ],
            }),
            getMockedTreeLabel({ name: 'dog', id: 'dog-label' }),
        ],
    });

    beforeEach(async () => {
        render(
            <LabelTreeViewItem
                item={item}
                save={saveHandler}
                addChild={addChildHandler}
                deleteItem={jest.fn()}
                projectLabels={[]}
                isCreationInNewProject={false}
                domains={domains}
                isEditable={true}
                isMixedRelation={false}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );
    });

    it("Open closed node - check if it's open", () => {
        fireEvent.click(screen.getByTestId('toggle-label-item'));

        expect(saveHandler).toHaveBeenCalledWith({ ...item, open: true }, item.id);
    });

    it("Add child to closed node - check if it's opened", () => {
        fireEvent.click(screen.getByTestId('animal-group-add-child-label-button'));

        expect(addChildHandler).toHaveBeenCalledWith(null, 'animal', LabelItemType.LABEL);
    });
});

describe('LabelTreeViewItem - menu', () => {
    describe('Creation', () => {
        const getItemComponent = (item: LabelTreeItem, domains: DOMAIN[], isMixedRelation = false): JSX.Element => (
            <LabelTreeViewItem
                item={item}
                save={saveHandler}
                addChild={jest.fn()}
                projectLabels={[]}
                deleteItem={jest.fn()}
                isCreationInNewProject={true}
                domains={domains}
                isEditable={true}
                isMixedRelation={isMixedRelation}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        it('Classification flat structure - delete', async () => {
            const item = getMockedTreeLabel({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.CLASSIFICATION]));

            expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();

            checkNumberOfMenuActions(item.id, 'label', 1);
        });

        it('Classification hierarchical structure - label - add group, delete', async () => {
            const item = getMockedTreeLabel({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.CLASSIFICATION], true));

            expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'add child group button' })).toBeInTheDocument();
            checkNumberOfMenuActions(item.id, 'label', 2);
        });

        it('Classification hierarchical structure - group - add label, delete', async () => {
            const item = getMockedTreeGroup({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.CLASSIFICATION], true));

            expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
            expect(screen.getByRole('button', { name: 'add child label button' })).toBeInTheDocument();
            checkNumberOfMenuActions(item.id, 'group', 2);
        });

        it('Detection - delete', async () => {
            const item = getMockedTreeLabel({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.DETECTION]));

            expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
            checkNumberOfMenuActions(item.id, 'label', 1);
        });

        it('Segmentation - delete', async () => {
            const item = getMockedTreeLabel({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.SEGMENTATION]));

            expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
            checkNumberOfMenuActions(item.id, 'label', 1);
        });
    });

    describe('Edition', () => {
        const getItemComponent = (item: LabelTreeItem, domains: DOMAIN[], isMixedRelation = false): JSX.Element => (
            <LabelTreeViewItem
                item={item}
                save={saveHandler}
                addChild={jest.fn()}
                deleteItem={jest.fn()}
                projectLabels={[]}
                isCreationInNewProject={false}
                domains={domains}
                isEditable={true}
                isMixedRelation={isMixedRelation}
                validationErrors={{}}
                setValidationError={jest.fn()}
            />
        );

        describe('Classification', () => {
            it('New group - add, delete', async () => {
                const item = getMockedTreeGroup({ name: 'test', state: LabelItemEditionState.NEW });

                render(getItemComponent(item, [DOMAIN.CLASSIFICATION]));

                expect(screen.getByRole('button', { name: 'add child label button' })).toBeInTheDocument();
                expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
                checkNumberOfMenuActions(item.id, 'group', 2);
            });

            it('Group - add, delete', async () => {
                const item = getMockedTreeGroup({ name: 'test', state: LabelItemEditionState.IDLE });

                render(getItemComponent(item, [DOMAIN.CLASSIFICATION]));

                expect(screen.getByRole('button', { name: 'add child label button' })).toBeInTheDocument();
                expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
                checkNumberOfMenuActions(item.id, 'group', 2);
            });

            it('Label hierarchical - add, delete', async () => {
                const item = getMockedTreeLabel({ name: 'test', state: LabelItemEditionState.IDLE });

                render(getItemComponent(item, [DOMAIN.CLASSIFICATION], true));

                expect(screen.getByRole('button', { name: 'add child group button' })).toBeInTheDocument();
                expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
                checkNumberOfMenuActions(item.id, 'label', 2);
            });
        });

        it('Edition - Detection - delete', async () => {
            const item = getMockedTreeLabel({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.DETECTION]));

            expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
            checkNumberOfMenuActions(item.id, 'label', 1);
        });

        it('Edition - Segmentation - delete', async () => {
            const item = getMockedTreeLabel({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.SEGMENTATION]));

            expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
            checkNumberOfMenuActions(item.id, 'label', 1);
        });

        it('Anomaly - no menu actions', async () => {
            const item = getMockedTreeLabel({ name: 'test' });

            render(getItemComponent(item, [DOMAIN.ANOMALY_CLASSIFICATION]));

            checkNumberOfMenuActions(item.id, 'label', 0);
        });

        describe('Task chain', () => {
            it('First task - label - delete', async () => {
                const item = getMockedTreeLabel({ name: 'test' });

                render(getItemComponent(item, [DOMAIN.DETECTION]));

                expect(screen.getByRole('button', { name: 'delete' })).toBeInTheDocument();
                checkNumberOfMenuActions(item.id, 'label', 1);
            });
        });
    });
});
