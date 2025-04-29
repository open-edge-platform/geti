// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export type Vec2 = { x: number; y: number };

export const add = (a: Vec2, b: Vec2): Vec2 => {
    return { x: a.x + b.x, y: a.y + b.y };
};

export const addScalar = (a: Vec2, b: number): Vec2 => {
    return { x: a.x + b, y: a.y + b };
};

export const sub = (a: Vec2, b: Vec2): Vec2 => {
    return { x: a.x - b.x, y: a.y - b.y };
};

export const subScalar = (a: Vec2, b: number): Vec2 => {
    return { x: a.x - b, y: a.y - b };
};

export const mul = (a: Vec2, b: Vec2): Vec2 => {
    return { x: a.x * b.x, y: a.y * b.y };
};

export const div = (a: Vec2, b: Vec2): Vec2 => {
    return { x: a.x / b.x, y: a.y / b.y };
};

export const mulScalar = (value: Vec2, scalar: number): Vec2 => {
    return {
        x: value.x * scalar,
        y: value.y * scalar,
    };
};

export const divScalar = (value: Vec2, scalar: number): Vec2 => {
    return {
        x: value.x / scalar,
        y: value.y / scalar,
    };
};

export const rotate = (vector: Vec2, radians: number): Vec2 => {
    return {
        x: vector.x * Math.cos(radians) - vector.y * Math.sin(radians),
        y: vector.x * Math.sin(radians) + vector.y * Math.cos(radians),
    };
};

export const magnitude = (value: Vec2): number => {
    return Math.sqrt(value.x * value.x + value.y * value.y);
};

export const normalize = (value: Vec2): Vec2 => {
    const magn = magnitude(value);
    return div(value, { x: magn, y: magn });
};

export const dot = (a: Vec2, b: Vec2): number => {
    return a.x * b.x + a.y * b.y;
};

export const sign = (value: Vec2): Vec2 => {
    return {
        x: value.x >= 0 ? 1 : -1,
        y: value.y >= 0 ? 1 : -1,
    };
};

export const roundTo = (value: Vec2, digits: number): Vec2 => {
    const factor = Math.pow(10, digits);
    return {
        x: Math.round(value.x * factor) / factor,
        y: Math.round(value.y * factor) / factor,
    };
};

export const abs = (value: Vec2): Vec2 => {
    return {
        x: Math.abs(value.x),
        y: Math.abs(value.y),
    };
};

export const toClipperPoint = ({ x, y }: Vec2): { X: number; Y: number } => {
    return { X: x, Y: y };
};

export const getAngle = (direction: Vec2): number => {
    return Math.atan2(direction.y, direction.x);
};

const radiansToDegrees = (radians: number): number => {
    return (radians * 180) / Math.PI;
};

export const getAngleDegrees = (direction: Vec2): number => {
    return radiansToDegrees(getAngle(direction));
};
