// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { DOMAIN } from '../projects/core.interface';
import { Group, Label, LabelsRelationType } from './label.interface';

export enum LabelItemEditionState {
    NEW = 'New',
    NEW_DEFAULT = 'New default',
    CHANGED = 'Changed',
    REMOVED = 'Removed',
    IDLE = 'Idle',
}

interface LabelTreeCommon {
    children: LabelTreeItem[];
    open: boolean;
    inEditMode: boolean;
    state: LabelItemEditionState;
    relation: LabelsRelationType;
}

export enum LabelItemType {
    LABEL = 'LABEL',
    GROUP = 'GROUP',
}

export type LabelTreeGroupProps = Group & LabelTreeCommon & { type: LabelItemType.GROUP };
export type LabelTreeLabelProps = Label & LabelTreeCommon & { type: LabelItemType.LABEL };

export type LabelTreeItem = LabelTreeLabelProps | LabelTreeGroupProps;

export interface TreeItemPresentationModeProps<T> {
    item: T;
    newTree: boolean;
}

export enum ValidationErrorType {
    TREE = 'tree',
    LABELS = 'labels',
}

export enum Readonly {
    YES,
    NO,
}

interface LabelTreeViewOptions {
    width?: number | string;
    newTree?: boolean;
}

interface SetTreeValidation {
    type: ValidationErrorType.TREE;
    validationError: string | undefined;
}

interface SetLabelsValidation {
    type: ValidationErrorType.LABELS;
    validationError: boolean;
}

export type SetValidationProps = SetTreeValidation | SetLabelsValidation;

export interface EditableTreeViewProps {
    labelsTree: LabelTreeItem[];
    projectLabels?: LabelTreeItem[];
    isHierarchicalMode: boolean;
    isInEditMode: boolean;
    save: (editedLabel?: LabelTreeItem, oldId?: string) => void;
    deleteItem: (deletedLabel: LabelTreeItem) => void;
    addChild: (parentId: string, groupName: string, type: LabelItemType) => void;
    domains: DOMAIN[];
    type: Readonly.NO;
    options?: LabelTreeViewOptions;
    setValidationError: (options: SetValidationProps) => void;
}

interface ReadonlyTreeView {
    labelsTree: LabelTreeItem[];
    projectLabels?: LabelTreeItem[];
    isHierarchicalMode: boolean;
    save?: never;
    deleteItem?: never;
    addChild?: never;
    domains?: never;
    type: Readonly.YES;
    options?: LabelTreeViewOptions;
}

export type LabelsTreeViewProps = EditableTreeViewProps | ReadonlyTreeView;

export interface CommonTreeViewProps {
    labels: LabelTreeItem[];
    isEditable: boolean;
    save: (editedLabel?: LabelTreeItem, oldId?: string) => void;
    addChild: (parentId: string | null, groupName: string, type: LabelItemType) => void;
    deleteItem: (deletedItem: LabelTreeItem) => void;
    projectLabels: LabelTreeItem[];
    domains: DOMAIN[];
    treeValidationErrors: Record<string, Record<string, string>>;
    setValidationError: (id: string, errors: Record<string, string>) => void;
}

export interface FlatLabelTreeViewProps extends CommonTreeViewProps {
    width?: number | string;
    isCreationInNewProject?: boolean;
}

export interface HierarchicalLabelTreeViewProps extends CommonTreeViewProps {
    level?: number;
    options?: LabelTreeViewOptions;
}
