import time
import numpy as np
from IPython.display import clear_output
from options.train_options import TrainOptions
from data.data_loader import load_data, minibatchAB
from data.data_display import show_generator_image
from models.train_function import get_train_function
from models.networks import resnet_generator, n_layer_discriminator, cycle_generater
from models.loss import netG_loss, netD_loss
from keras.layers import Input

opt = TrainOptions().parse()

# load data
train_A = load_data(opt.dataroot + 'trainA/*')
train_B = load_data(opt.dataroot + 'trainB/*')
print('#training images = {}'.format(len(train_A)))
train_batch = minibatchAB(train_A, train_B, opt.batch_size)

# create gennerator models
netG_A, netG_A_real_A, netG_A_fake_B = resnet_generator()
netG_B, netG_B_real_B, netG_B_fake_A = resnet_generator()
netG_A.summary()

# create discriminator models
netD_A = n_layer_discriminator()
netD_B = n_layer_discriminator()
netD_A.summary()

# create generator train function
netD_A_predict_netG_fake = netD_A(netG_B_fake_A)
netD_B_predict_netG_fake = netD_B(netG_A_fake_B)
rec_A = netG_B(netG_A_fake_B)
rec_B = netG_A(netG_B_fake_A)
lambda_layer_inputs = [netD_A_predict_netG_fake, rec_A, netG_A_real_A, netD_B_predict_netG_fake, rec_B, netG_B_real_B]
netG_train_function = get_train_function(inputs=[netG_A_real_A, netG_B_real_B], loss_function=netG_loss,
                                         lambda_layer_inputs=lambda_layer_inputs)

# create discriminator A train function
image_size = opt.fine_size
input_nc = opt.input_nc

real_A = Input(shape=(image_size, image_size, input_nc))
fake_A = Input(shape=(image_size, image_size, input_nc))
netD_A_predict_real = netD_A(real_A)
netD_A_predict_fake = netD_A(fake_A)
lambda_layer_inputs = [netD_A_predict_real, netD_A_predict_fake]
netD_A_train_function = get_train_function(inputs=[real_A, fake_A], loss_function=netD_loss,
                                           lambda_layer_inputs=lambda_layer_inputs)
# create discriminator B train function
real_B = Input(shape=(image_size, image_size, input_nc))
fake_B = Input(shape=(image_size, image_size, input_nc))
netD_B_predict_real = netD_B(real_B)
netD_B_predict_fake = netD_B(fake_B)
lambda_layer_inputs = [netD_B_predict_real, netD_B_predict_fake]
netD_B_train_function = get_train_function(inputs=[real_B, fake_B], loss_function=netD_loss,
                                           lambda_layer_inputs=lambda_layer_inputs)
# create fake_image and rec_image generator
cycle_A_generater = cycle_generater(netG_A, netG_B)
cycle_B_generater = cycle_generater(netG_B, netG_A)


# train loop
path = opt.dataroot
time_start = time.time()
niter = 5
gen_iterations = 0
epoch = 0
batch_size = 1
display_iters = 5000
# val_batch = minibatch(val_A, val_B, batch_size)
train_batch = minibatchAB(train_A, train_B, batch_size)

while epoch < niter:
    target_label = np.zeros((batch_size, 1))
    epoch, real_A, real_B = next(train_batch)
    # generate fake_A, fake_B
    f_B = cycle_A_generater([A])[0]
    f_A = cycle_B_generater([B])[0]

    netG_train_function.train_on_batch([real_A, real_B], target_label)

    fake_B = netG_A.predictict(real_A)
    fake_A = netG_B.predictict(real_B)

    netD_A_train_function.train_on_batch([real_A, fake_A], target_label)
    netD_B_train_function.train_on_batch([real_B, fake_B], target_label)

    gen_iterations += 1

    if gen_iterations % display_iters == 0:
        clear_output()
        traintime = (time.time() - time_start) / gen_iterations
        print('epoch: {}/{}  iter_count: {}  timecost/iter: {}s'.format(epoch, niter, gen_iterations, traintime))
        _, A, B = train_batch.send(4)
        show_generator_image(A, B, netG_A, netG_B)

        save_name = path + '{}' + str(gen_iterations) + '{}'
        netG_A.save(save_name.format('tf_GA', '.h5'))
        netG_A.save_weights(save_name.format('tf_GA_weights', '.h5'))
        netG_B.save(save_name.format('tf_GB', '.h5'))
        netG_B.save_weights(save_name.format('tf_GB_weights', '.h5'))
        netD_A.save(save_name.format('tf_DA', '.h5'))
        netD_A.save_weights(save_name.format('tf_DA_weights', '.h5'))
        netD_B.save(save_name.format('tf_DB', '.h5'))
        netD_B.save_weights(save_name.format('tf_DB_weights', '.h5'))
