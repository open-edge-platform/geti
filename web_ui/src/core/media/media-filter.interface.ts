// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum SortMenuActionKey {
    NAME = 'Media Name',
    DATE = 'Media Upload Date',
    SIZE = 'Media size',
    ANNOTATION_DATE = 'Annotation Creation Date',
}

export interface AdvancedFilterSortingOptions {
    sortBy?: string;
    sortDir?: string;
}

// Note: condition = undefined is only when we add an empty filter rule
export interface MediaFilterOptions {
    condition: 'and' | 'or' | 'nor' | undefined;
    rules: SearchOptionsRule[];
}

export type AdvancedFilterOptions = Record<string, never> | MediaFilterOptions;

export interface SearchOptionsRule {
    id: string;
    field: SearchRuleField | '';
    operator: SearchRuleOperator | '';
    value: SearchRuleValue;
}

export type SearchRuleValue = string | string[] | number | null;

export enum SearchRuleField {
    LabelId = 'LABEL_ID',
    MediaName = 'MEDIA_NAME',
    MediaWidth = 'MEDIA_WIDTH',
    MediaUploadDate = 'MEDIA_UPLOAD_DATE',
    MediaHeight = 'MEDIA_HEIGHT',
    MediaType = 'MEDIA_TYPE',
    MediaSize = 'MEDIA_SIZE',
    AnnotationCreationDate = 'ANNOTATION_CREATION_DATE',
    AnnotationSceneState = 'ANNOTATION_SCENE_STATE',
    ShapeType = 'SHAPE_TYPE',
    ShapeAreaPercentage = 'SHAPE_AREA_PERCENTAGE',
    ShapeAreaPixel = 'SHAPE_AREA_PIXEL',
    UserName = 'USER_NAME',
    Score = 'SCORE',
    Subset = 'SUBSET',
}

export enum SearchRuleOperator {
    In = 'IN',
    Less = 'LESS',
    Equal = 'EQUAL',
    NotIn = 'NOT_IN',
    Greater = 'GREATER',
    NotEqual = 'NOT_EQUAL',
    LessOrEqual = 'LESS_OR_EQUAL',
    GreaterOrEqual = 'GREATER_OR_EQUAL',
    Contains = 'CONTAINS',
}

export enum AnnotationSceneState {
    NONE = 'NONE',
    REVISIT = 'TO_REVISIT',
    ANNOTATED = 'ANNOTATED',
    PARTIALLY_ANNOTATED = 'PARTIALLY_ANNOTATED',
}

export enum SearchRuleShapeType {
    ELLIPSE = 'ELLIPSE',
    RECTANGLE = 'RECTANGLE',
    POLYGON = 'POLYGON',
}

export enum SearchRuleMediaType {
    IMAGE = 'IMAGE',
    VIDEO = 'VIDEO',
}

export enum SearchOptionsActionsType {
    ADD = 'ADD',
    RESET = 'RESET',
    UPDATE = 'UPDATE',
    REMOVE = 'REMOVE',
    UPDATE_ALL = 'UPDATE_ALL',
    REMOVE_ALL = 'REMOVE_ALL',
}

export type SearchOptionsActions =
    | { type: SearchOptionsActionsType.ADD }
    | { type: SearchOptionsActionsType.REMOVE_ALL }
    | { type: SearchOptionsActionsType.RESET; id: string }
    | { type: SearchOptionsActionsType.REMOVE; id: string }
    | { type: SearchOptionsActionsType.UPDATE; id: string; rule: SearchOptionsRule }
    | { type: SearchOptionsActionsType.UPDATE_ALL; filterOptions: AdvancedFilterOptions };

export interface ShapeOption {
    text: string;
    key: SearchRuleShapeType;
}

export interface MediaTypeOption {
    text: string;
    key: SearchRuleMediaType;
}
export interface FilterItems {
    text: string;
    key: SearchRuleField;
}

export interface SearchOptionsRuleDTO {
    field: string;
    operator: string;
    value: SearchRuleValue;
}
