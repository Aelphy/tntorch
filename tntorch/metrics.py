import torch
import numpy as np
import tntorch as tn


def _process(gt, approx):
    """
    If only one of the arguments is a compressed tensor, we decompress it
    """

    assert np.array_equal(gt.shape, approx.shape)
    is1 = isinstance(gt, tn.Tensor)
    is2 = isinstance(approx, tn.Tensor)
    if is1 and is2:
        return gt, approx
    if is1:
        gt = gt.full()
    if is2:
        approx = approx.full()
    return gt, approx


def dot(t1, t2, k=None):  # TODO support partial dot products
    """
    Computes the dot product between two tensors.

    :param t1: a tensor
    :param t2: a tensor
    :return: a scalar

    """

    t1, t2 = _process(t1, t2)
    if isinstance(t1, torch.Tensor) and isinstance(t2, torch.Tensor):
        return t1.flatten().dot(t2.flatten())

    assert np.array_equal(t1.shape, t2.shape)

    if k is None:
        k = min(t1.ndim, t2.ndim)
    Lprod = torch.ones([1, 1])
    for mu in range(t1.ndim-1, t1.ndim-1-k, -1):
        core1 = t1.cores[mu]
        if t1.Us[mu] is None:
            core2 = t2.cores[mu]
            if t2.Us[mu] is not None:
                core1 = torch.einsum('ijk,ja->iak', (core1, t2.Us[mu]))
        elif t2.Us[mu] is None:
            core2 = torch.einsum('ijk,ja->iak', (t2.cores[mu], t1.Us[mu]))
        else:
            core2 = torch.einsum('ijk,ar,aj->irk', (t2.cores[mu], t1.Us[mu], t2.Us[mu]))
        Ucore = torch.einsum('ijk,ka->ija', (core1, Lprod))
        Vcore = core2
        Lprod = torch.mm(Ucore.reshape([Ucore.shape[0], -1]), torch.t(Vcore.reshape([Vcore.shape[0], -1])))
    return torch.squeeze(Lprod)


def distance(t1, t2):
    """
    Computes the Euclidean distance between two tensors. Generally faster than tn.norm(t1-t2).

    :param t1: a tensor
    :param t2: a tensor
    :return: a scalar >= 0

    """

    t1, t2 = _process(t1, t2)
    if isinstance(t1, torch.Tensor) and isinstance(t2, torch.Tensor):
        return torch.norm(t1-t2)
    return torch.sqrt(tn.dot(t1, t1) + tn.dot(t2, t2) - 2 * tn.dot(t1, t2).clamp(0))


def relative_error(gt, approx):
    """
    Computes the relative error between two tensors (torch or tntorch).

    :param gt: a torch or tntorch tensor
    :param approx: a torch or tntorch tensor
    :return: a scalar >= 0

    """

    gt, approx = _process(gt, approx)
    if isinstance(gt, torch.Tensor) and isinstance(approx, torch.Tensor):
        return torch.norm(gt-approx) / torch.norm(gt)
    dotgt = tn.dot(gt, gt)
    return torch.sqrt((dotgt + tn.dot(approx, approx) - 2*tn.dot(gt, approx)).clamp(0)) / torch.sqrt(dotgt.clamp(0))


def rmse(gt, approx):
    """
    Computes the RMSE between two tensors (torch or tntorch).

    :param gt: a torch or tntorch tensor
    :param approx: a torch or tntorch tensor
    :return: a scalar >= 0

    """

    gt, approx = _process(gt, approx)
    if isinstance(gt, torch.Tensor) and isinstance(approx, torch.Tensor):
        return torch.norm(gt-approx) / np.sqrt(gt.numel())
    return tn.distance(gt, approx) / torch.sqrt(gt.size)


def r_squared(gt, approx):
    """
    Computes the R^2 score between two tensors (torch or tntorch).

    :param gt: a torch or tntorch tensor
    :param approx: a torch or tntorch tensor
    :return: a scalar <= 1

    """

    gt, approx = _process(gt, approx)
    if isinstance(gt, torch.Tensor) and isinstance(approx, torch.Tensor):
        return 1 - torch.norm(gt-approx)**2 / torch.norm(gt-torch.mean(gt))**2
    return 1 - tn.distance(gt, approx)**2 / tn.normsq(gt-tn.mean(gt))