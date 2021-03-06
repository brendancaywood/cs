#include "./include/ChatClient.hpp"
#include "./include/User.hpp"
#include "./include/Succ.hpp"
#include "./include/Crypto.hpp"

#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <openssl/conf.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/rand.h>
#include <sys/socket.h>
#include <tuple>
#include <unistd.h>

void* client::ChatClient::client_handler(void* args) {
  the::Succ SLIP_SLOP;
  yep::Crypto JEFF;
  ChatClient::thread t;
  ChatClient::std_message s;
  std::memcpy(&t, args, sizeof(ChatClient::thread));

  std::string data;
  while (data != "/quit" && data != "kicked") {

    char buf[4096];
    std::memset(buf, 0, sizeof(buf));
    int inlen = recv(t.socket, buf, 4096, 0);
    // Decrypt our message
    unsigned char* ciphertext = (unsigned char*)buf;

    unsigned char miv[16];
    std::memset(miv, 0, 16);

    unsigned char plaintext[1024];
    std::memset(plaintext, 0, 1024);
    
    int plaintext_len = JEFF.decrypt(ciphertext, inlen, t.key, miv, plaintext);

    
    data = std::string((char *)plaintext);
    if (data == "kicked") {
      std::cout << "OHH HO HO HOOO YOU HAVE BEEN KICKED MY BOY" << std::endl;
      exit(0);
      return nullptr;
    }
    std::cout << " <<< " << data << "\n <<< " << std::endl;
  }

  return nullptr;
}
namespace client {

in_addr_t ChatClient::handle_host() {
  std::cout << "Please enter the host you would like to connect to: " << std::flush;
  std::string host = "";
  std::getline(std::cin, host);

  return inet_addr(host.c_str());
}

int ChatClient::handle_port() {
  std::cout << "Please enter the port to connect from: " << std::flush;
  std::string port = "";
  std::getline(std::cin, port);

  return std::stoi(port);
}


std::string ChatClient::handle_input() {
  std::cout << " >>> " << std::flush;
  std::string message = "";
  std::getline(std::cin, message);

  return message;
}

int ChatClient::RunClient() {
  int sockfd = socket(AF_INET, SOCK_STREAM, 0);

  if (sockfd < 0) {
    std::cerr << "Error creating the socket" << std::endl;
    return EXIT_FAILURE;
  }
  int port = handle_port();
  in_addr_t host = handle_host();

  struct sockaddr_in server;
  server.sin_family = AF_INET;
  server.sin_port = htons(port);
  server.sin_addr.s_addr = host;

  socklen_t sin_size = sizeof server;

  int c = connect(sockfd, reinterpret_cast<sockaddr*>(&server), sin_size);
  if (c < 0) {
    std::cerr << "Error connecting" << std::endl;
    return EXIT_FAILURE;
  }

  std::cout << "You connected." << std::endl;

  std::string username = "";
  ChatClient::symmetric_key_message skm;
  int taken = 1;
  bool kicked = false;

  /*
   CRYPTO GARBAGE BEGINS HERE ===========================================
  */

  yep::Crypto JEFF;

  unsigned char key[32];
  unsigned char iv[16];

  OpenSSL_add_all_algorithms();

  RAND_bytes(key, 32);
  RAND_bytes(iv,16);

  std::cout << "this is the key: " << key << std::endl;
  
  // get that pubkey
  EVP_PKEY *pubkey;
  FILE* pubf = fopen("rsa_pub.pem","rb");
  pubkey = PEM_read_PUBKEY(pubf,nullptr,nullptr,nullptr);

  std::cout << key << std::endl;

  unsigned char encrypted_key[256];
  std::memset(encrypted_key, 0, 256);
  int encryptedkey_len = JEFF.rsa_encrypt(key, 32, pubkey, encrypted_key);

  std::cout << encryptedkey_len << std::endl;

  // send encrypted key to server
  int len = sendto(sockfd, &encrypted_key, encryptedkey_len, 0, reinterpret_cast<sockaddr*>(&server), sin_size);

  std::cout << len << std::fflush;

  /*
   END MY LIFE =======================================================
  */

  std::cout << "Please enter a username" << std::endl;
  std::getline(std::cin, username);
  sendto(sockfd, username.c_str(), username.length(), 0, reinterpret_cast<sockaddr*>(&server), sin_size);

  // Allocate space on the heap
  ChatClient::thread *t = new ChatClient::thread;
  std::memcpy(&t->socket, &sockfd, sizeof(int));
  std::memcpy(&t->key, &key, 32);

  
  pthread_t child;
  pthread_create(&child, nullptr, client_handler, t);
  pthread_detach(child);

  while (true) {
    ChatClient::std_message s_message;
    std::string message = handle_input();

    if (message == "/quit\n" && !kicked) {
      break;
    }

    unsigned char* plaintext = (unsigned char*)message.c_str();

    unsigned char miv[16];
    //RAND_bytes(miv, 16);

    std::memset(miv, 0, 16);
    
    unsigned char ciphertext[1024];
    std::memset(ciphertext,0,1024);
    int ciphertext_len = JEFF.encrypt(plaintext, message.size(), key, miv, ciphertext);

    send(sockfd, ciphertext, ciphertext_len, 0);
  }

  close(sockfd);

  return EXIT_SUCCESS;
}

} // namespace client


int main() {
  client::ChatClient cs;
  cs.RunClient();

  return EXIT_SUCCESS;
}
